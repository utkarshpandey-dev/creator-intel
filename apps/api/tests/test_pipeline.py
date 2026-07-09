"""Unit tests for the comment-pipeline stages (pure, no DB/API)."""

import asyncio
import os

import numpy as np
import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("INTERNAL_API_SECRET", "test-internal-secret")

from app.ai.embeddings import DeterministicEmbeddingProvider  # noqa: E402
from app.pipeline import filtering, sentiment  # noqa: E402
from app.pipeline.assembly import assemble_clusters  # noqa: E402
from app.pipeline.clustering import choose_k, cluster_vectors  # noqa: E402
from app.pipeline.dedupe import group_by_hash  # noqa: E402
from app.pipeline.representatives import classify_theme, nearest_exemplars  # noqa: E402


# --- filtering ---
@pytest.mark.parametrize(
    "text,kept",
    [
        ("This tutorial really helped me understand recursion", True),
        ("🔥🔥🔥", False),
        ("sub for sub", False),
        ("check out my channel please", False),
        ("http://spam.example.com free money", False),
        ("nice", False),  # too short (< 3 words)
        ("", False),
    ],
)
def test_filtering(text, kept):
    assert filtering.should_keep(text, min_words=3) is kept


# --- sentiment ---
def test_sentiment_direction():
    assert sentiment.score("I love this, it was amazing and helpful") > 0
    assert sentiment.score("this was boring and confusing, worst video") < 0
    assert sentiment.score("the video is about python") == 0.0


def test_sentiment_negation():
    assert sentiment.score("not good") < 0


# --- dedupe ---
def test_group_by_hash_collapses():
    items = [("a", "h1"), ("b", "h1"), ("c", "h2")]
    groups = group_by_hash(items)
    assert groups["h1"] == ["a", "b"]
    assert groups["h2"] == ["c"]


# --- clustering ---
def test_choose_k_bounds():
    assert choose_k(1, 80) == 1
    assert choose_k(2, 80) == 1
    assert 2 <= choose_k(100, 80) <= 80
    assert choose_k(1000, 10) == 10


def test_cluster_two_blobs():
    rng = np.random.default_rng(0)
    blob_a = rng.normal(loc=[5, 0], scale=0.1, size=(20, 2))
    blob_b = rng.normal(loc=[-5, 0], scale=0.1, size=(20, 2))
    vectors = np.vstack([blob_a, blob_b])
    labels, centroids = cluster_vectors(vectors, k=2)
    # The two blobs should end up in different clusters.
    assert len(set(labels[:20])) == 1
    assert len(set(labels[20:])) == 1
    assert labels[0] != labels[-1]
    assert centroids.shape == (2, 2)


# --- representatives ---
def test_classify_theme():
    assert classify_theme("please make a tutorial on this", 0.5) == "request"
    assert classify_theme("this was terrible", -0.6) == "complaint"
    assert classify_theme("absolutely loved it", 0.8) == "praise"
    assert classify_theme("the video is 10 minutes", 0.0) == "other"


def test_nearest_exemplars_picks_closest():
    centroid = np.array([1.0, 0.0])
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])
    texts = ["closest", "far", "close"]
    result = nearest_exemplars(vectors, centroid, texts, n=2)
    assert result[0] == "closest"
    assert "far" not in result


# --- deterministic embeddings ---
def test_deterministic_embeddings_stable_and_normalized():
    provider = DeterministicEmbeddingProvider(dim=64)
    v1 = asyncio.run(provider.embed(["hello world"]))[0]
    v2 = asyncio.run(provider.embed(["hello world"]))[0]
    assert v1 == v2  # deterministic
    assert len(v1) == 64
    assert abs(np.linalg.norm(v1) - 1.0) < 1e-6  # unit length


# --- assembly (the numeric core the DB orchestrator delegates to) ---
def test_assemble_clusters_end_to_end():
    rng = np.random.default_rng(1)
    # Two clearly separated topics, 15 comments each.
    topic_a = rng.normal(loc=[10, 0, 0], scale=0.05, size=(15, 3))
    topic_b = rng.normal(loc=[0, 10, 0], scale=0.05, size=(15, 3))
    vectors = np.vstack([topic_a, topic_b])
    texts = [f"a{i}" for i in range(15)] + [f"b{i}" for i in range(15)]
    weights = [1] * 30
    sentiments = [0.5] * 15 + [-0.5] * 15

    results = assemble_clusters(
        texts, weights, sentiments, vectors, max_clusters=80, min_comments_to_cluster=5
    )

    # Every comment lands in exactly one cluster; sizes sum to total weight.
    assigned = sorted(i for r in results for i in r.member_indices)
    assert assigned == list(range(30))
    assert sum(r.size for r in results) == 30
    assert len(results) >= 2
    for r in results:
        assert len(r.centroid) == 3
        assert r.label is not None
