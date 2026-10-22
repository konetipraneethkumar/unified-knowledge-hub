import type { ChatSource } from "../types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const accessTokenKey = "ukh_access_token";

type ApiItem = {
  id: number;
  source: string;
  title: string | null;
  item_type: string | null;
  summary: string | null;
  modified_at: string | null;
  indexed_at: string;
};

type SearchPayload = { query: string; total: number; items: ApiItem[] };

export async function searchKnowledge(query: string): Promise<{ answer: string; sources: ChatSource[] }> {
  const token = window.localStorage.getItem(accessTokenKey);
  if (!token) throw new Error("Sign in to search your knowledge.");
  const response = await fetch(`${apiBaseUrl}/search?${new URLSearchParams({ q: query, limit: "10" })}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json().catch(() => null) as SearchPayload | { detail?: string } | null;
  if (!response.ok) throw new Error((payload as { detail?: string } | null)?.detail ?? "Search is temporarily unavailable.");
  const result = payload as SearchPayload;
  const sources = result.items.map((item) => ({
    id: String(item.id),
    title: item.title ?? "Untitled resource",
    type: item.item_type ?? "Resource",
    summary: item.summary ?? "No approved summary is available.",
    category: item.source,
    date: new Date(item.modified_at ?? item.indexed_at).toLocaleDateString(),
  }));
  return {
    answer: sources.length ? `${result.total} matching resource${result.total === 1 ? "" : "s"} found.` : "No matching indexed resources were found.",
    sources,
  };
}
