import { apiRequest } from "../auth/api";
import { getAccessToken } from "../auth/AuthContext";

export type KnowledgeItem = {
  id: number;
  connector_id: string | null;
  source: string;
  source_item_id: string;
  title: string | null;
  item_type: string | null;
  mime_type: string | null;
  file_size_bytes: number | null;
  location: string | null;
  parent_location: string | null;
  web_url: string | null;
  file_path: string | null;
  source_metadata: Record<string, unknown> | null;
  summary: string | null;
  processing_status: string;
  processing_error: string | null;
  created_at: string;
  modified_at: string | null;
  indexed_at: string;
};

export type KnowledgePage = {
  offset: number;
  limit: number;
  total: number;
  items: KnowledgeItem[];
};

export type Connector = {
  id: string;
  connector_type: string;
  provider: string;
  name: string;
  status: string;
  authentication_status: string;
  authorized_root: string | null;
  external_account_id: string | null;
  indexed_item_count: number | null;
  last_sync_at: string | null;
  revoked_at: string | null;
};

export type PairedDevice = {
  id: string;
  name: string;
  created_at: string;
  last_seen_at: string | null;
  revoked_at: string | null;
};

export type ConnectorSyncResult = {
  connector_id: string;
  status: string;
  processed: number;
  skipped: number;
  failed: number;
  deleted: number;
  errors: string[];
};

export type SearchHistoryEntry = {
  id: number;
  query: string;
  mode: "ask" | "search";
  result_count: number;
  source_count: number;
  created_at: string;
};

export type SyncActivity = {
  id: number;
  connector_id: string | null;
  connector_name: string;
  connector_type: string;
  status: string;
  processed: number | null;
  skipped: number | null;
  failed: number | null;
  deleted: number | null;
  created_at: string;
};

export type WorkspacePreferences = {
  saveSearchHistory: boolean;
  knowledgePageSize: number;
  searchMode: "ask" | "search";
  resultCount: number;
  showEvidence: boolean;
  theme: "light" | "dark";
};

const defaultPreferences: WorkspacePreferences = {
  saveSearchHistory: true,
  knowledgePageSize: 20,
  searchMode: "ask",
  resultCount: 10,
  showEvidence: true,
  theme: "light",
};

function scopedKey(userId: number, key: string) {
  return `smriti.user.${userId}.${key}`;
}

export async function workspaceRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Your session has expired. Please sign in again.");
  }
  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return apiRequest<T>(path, { ...options, headers });
}

export function readPreferences(userId: number): WorkspacePreferences {
  try {
    const value = localStorage.getItem(scopedKey(userId, "preferences"));
    if (!value) return defaultPreferences;
    const parsed: unknown = JSON.parse(value);
    if (typeof parsed !== "object" || parsed === null) return defaultPreferences;
    const saved = parsed as Partial<WorkspacePreferences>;
    return {
      saveSearchHistory: saved.saveSearchHistory !== false,
      knowledgePageSize:
        saved.knowledgePageSize === 10 ||
        saved.knowledgePageSize === 20 ||
        saved.knowledgePageSize === 50
          ? saved.knowledgePageSize
          : defaultPreferences.knowledgePageSize,
      searchMode: saved.searchMode === "search" ? "search" : "ask",
      resultCount:
        saved.resultCount === 5 || saved.resultCount === 10 || saved.resultCount === 20
          ? saved.resultCount
          : defaultPreferences.resultCount,
      showEvidence: saved.showEvidence !== false,
      theme: saved.theme === "dark" ? "dark" : "light",
    };
  } catch {
    return defaultPreferences;
  }
}

export function writePreferences(userId: number, preferences: WorkspacePreferences) {
  localStorage.setItem(scopedKey(userId, "preferences"), JSON.stringify(preferences));
  window.dispatchEvent(
    new CustomEvent("smriti-preferences-changed", { detail: { userId } }),
  );
}

export function listKnowledgePage(options: {
  offset: number;
  limit: number;
  query: string;
  source: string;
  itemType: string;
  dateFrom: string;
  dateTo: string;
}) {
  const params = new URLSearchParams({
    offset: String(options.offset),
    limit: String(options.limit),
  });
  if (options.query.trim()) params.set("q", options.query.trim());
  if (options.source) params.set("source", options.source);
  if (options.itemType) params.set("item_type", options.itemType);
  if (options.dateFrom) params.set("date_from", options.dateFrom);
  if (options.dateTo) params.set("date_to", options.dateTo);
  return workspaceRequest<KnowledgePage>(`/knowledge-items/page?${params.toString()}`);
}

export function listKnowledgeSources() {
  return workspaceRequest<string[]>("/knowledge-items/sources");
}

export function listPairedDevices() {
  return workspaceRequest<PairedDevice[]>("/devices");
}

export function listKnowledgeItemTypes() {
  return workspaceRequest<string[]>("/knowledge-items/item-types");
}

export function listSearchHistory() {
  return workspaceRequest<SearchHistoryEntry[]>("/api/v1/activity/search-history");
}

export function createSearchHistory(
  query: string,
  mode: "ask" | "search",
  resultCount: number,
  sourceCount: number,
) {
  return workspaceRequest<SearchHistoryEntry>("/api/v1/activity/search-history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      mode,
      result_count: resultCount,
      source_count: sourceCount,
    }),
  });
}

export function clearSearchHistory() {
  return workspaceRequest<void>("/api/v1/activity/search-history", {
    method: "DELETE",
  });
}

export function listSyncActivity() {
  return workspaceRequest<SyncActivity[]>("/api/v1/activity/sync");
}
