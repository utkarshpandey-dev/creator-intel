import { apiFetch } from "./api";
import type { Channel, Insight, Report, Video } from "./types";

// Server-side data loaders. Each tolerates a backend that is down or a channel whose
// analysis hasn't been generated yet — the dashboard degrades gracefully instead of 500ing.

async function safeJson<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await apiFetch(path);
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export const getChannels = () => safeJson<Channel[]>("/youtube/channels", []);

export const getChannel = async (id: string): Promise<Channel | null> => {
  const channels = await getChannels();
  return channels.find((c) => c.id === id) ?? null;
};

export const getInsight = (id: string) =>
  safeJson<Insight | null>(`/channels/${id}/insights`, null);

export const getReports = (id: string) =>
  safeJson<Report[]>(`/channels/${id}/reports`, []);

export const getVideos = (id: string) =>
  safeJson<Video[]>(`/channels/${id}/videos`, []);
