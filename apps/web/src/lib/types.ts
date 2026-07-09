export type Scores = {
  health: number;
  engagement: number;
  growth: number;
  consistency: number;
  sentiment: number;
};

export type ThemeRef = { label: string | null; size: number | null; summary?: string | null };
export type TopicRef = { label: string | null; size: number | null; sentiment: number | null };

export type InsightPayload = {
  scores: Scores;
  audience_requests: ThemeRef[];
  audience_complaints: ThemeRef[];
  best_topics: TopicRef[];
  worst_topics: TopicRef[];
  video_count: number;
  theme_count: number;
};

export type Insight = {
  id: string;
  kind: string;
  payload: InsightPayload;
  created_at: string;
};

export type Report = {
  id: string;
  kind: string;
  title: string | null;
  content_md: string | null;
  payload: { scores?: Scores } | null;
  created_at: string;
};

export type Video = {
  id: string;
  title: string | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  published_at: string | null;
  thumbnail_url: string | null;
};

export type Channel = {
  id: string;
  title: string | null;
  handle: string | null;
  thumbnail_url: string | null;
  subscriber_count: number | null;
  video_count: number | null;
  last_synced_at: string | null;
};
