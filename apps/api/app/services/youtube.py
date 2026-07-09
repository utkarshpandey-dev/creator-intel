"""Async client for Google OAuth + the YouTube Data API v3.

Kept deliberately thin: it speaks HTTP and returns parsed JSON/dataclasses. Persistence,
tenancy, and quota policy live in the repositories and worker jobs that call it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from ..config import get_settings

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_API = "https://www.googleapis.com/youtube/v3"

_ISO_DURATION = re.compile(
    r"P(?:(?P<days>\d+)D)?T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?"
)


@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_in: int
    scope: str | None


def build_authorize_url(state: str) -> str:
    """The URL we send the creator to in order to grant access."""
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.youtube_scopes),
        "access_type": "offline",  # request a refresh token
        "prompt": "consent",  # ensure a refresh token is returned on reconnect
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def parse_iso8601_duration(value: str | None) -> int | None:
    if not value:
        return None
    m = _ISO_DURATION.fullmatch(value)
    if not m:
        return None
    parts = {k: int(v) for k, v in m.groupdict(default="0").items()}
    return parts["days"] * 86400 + parts["h"] * 3600 + parts["m"] * 60 + parts["s"]


class YouTubeClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._settings = get_settings()

    # --- OAuth ---
    async def exchange_code(self, code: str) -> OAuthTokens:
        resp = await self._client.post(
            _TOKEN_URL,
            data={
                "code": code,
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret,
                "redirect_uri": self._settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        d = resp.json()
        return OAuthTokens(
            access_token=d["access_token"],
            refresh_token=d.get("refresh_token"),
            expires_in=d.get("expires_in", 3600),
            scope=d.get("scope"),
        )

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        resp = await self._client.post(
            _TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": self._settings.google_client_id,
                "client_secret": self._settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        d = resp.json()
        # Google does not return a new refresh token on refresh; keep the existing one.
        return OAuthTokens(
            access_token=d["access_token"],
            refresh_token=d.get("refresh_token"),
            expires_in=d.get("expires_in", 3600),
            scope=d.get("scope"),
        )

    # --- Data API ---
    async def _get(self, access_token: str, path: str, params: dict) -> dict:
        resp = await self._client.get(
            f"{_API}/{path}",
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_my_channel(self, access_token: str) -> dict | None:
        data = await self._get(
            access_token,
            "channels",
            {"part": "snippet,statistics,contentDetails", "mine": "true"},
        )
        items = data.get("items", [])
        return items[0] if items else None

    async def list_upload_video_ids(
        self, access_token: str, uploads_playlist_id: str, max_videos: int
    ) -> list[str]:
        video_ids: list[str] = []
        page_token: str | None = None
        while len(video_ids) < max_videos:
            params = {
                "part": "contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": 50,
            }
            if page_token:
                params["pageToken"] = page_token
            data = await self._get(access_token, "playlistItems", params)
            for item in data.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    video_ids.append(vid)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return video_ids[:max_videos]

    async def get_videos(self, access_token: str, video_ids: list[str]) -> list[dict]:
        results: list[dict] = []
        for i in range(0, len(video_ids), 50):  # videos.list accepts up to 50 ids
            batch = video_ids[i : i + 50]
            data = await self._get(
                access_token,
                "videos",
                {"part": "snippet,statistics,contentDetails", "id": ",".join(batch)},
            )
            results.extend(data.get("items", []))
        return results

    async def list_video_comments(
        self, access_token: str, video_id: str, max_comments: int
    ) -> list[dict]:
        comments: list[dict] = []
        page_token: str | None = None
        while len(comments) < max_comments:
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": 100,
                "order": "relevance",
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token
            try:
                data = await self._get(access_token, "commentThreads", params)
            except httpx.HTTPStatusError as exc:
                # Comments disabled on a video → 403. Skip it, don't fail the whole import.
                if exc.response.status_code == 403:
                    break
                raise
            comments.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return comments[:max_comments]
