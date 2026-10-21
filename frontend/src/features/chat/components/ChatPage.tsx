import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useLocation, useSearchParams } from "react-router";
import { Button } from "../../../components/ui/Button";
import { ApiError, postJson } from "../../auth/api";
import { getAccessToken, useAuth } from "../../auth/AuthContext";
import { suggestedQueries } from "../data/suggestedQueries";
import { ChatWindow } from "./ChatWindow";
import type { ChatMessage, RagAnswerResponse } from "../types";
import {
  createSearchHistory,
  readPreferences,
  writePreferences,
  workspaceRequest,
  type KnowledgeItem,
} from "../../workspace/api";
import type { ChatSource } from "../types";

type RankedSearchResponse = {
  query: string;
  limit: number;
  total: number;
  items: { item: KnowledgeItem; relevance_score: number }[];
};

function toSearchSource(item: KnowledgeItem, relevanceScore: number): ChatSource {
  return {
    source_id: item.source_item_id,
    source_type: item.source,
    title: item.title,
    date: item.modified_at || item.indexed_at,
    evidence: item.summary || "",
    evidence_label: "Indexed summary",
    relevance_score: relevanceScore,
    trusted_source_reference: {
      location: item.location,
      web_url: item.web_url,
      file_path: item.file_path,
      parent_location: item.parent_location,
      metadata: item.source_metadata,
    },
  };
}

function createMessageId() {
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

export function ChatPage() {
  const { user } = useAuth();
  const reduceMotion = useReducedMotion() ?? false;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [retryQuery, setRetryQuery] = useState<string | null>(null);
  const [retryMode, setRetryMode] = useState<"ask" | "search">("ask");
  const [mode, setMode] = useState<"ask" | "search">(() =>
    user ? readPreferences(user.id).searchMode : "ask",
  );
  const [resultCount, setResultCount] = useState(() =>
    user ? readPreferences(user.id).resultCount : 10,
  );
  const [historyError, setHistoryError] = useState("");
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const handledLocationKey = useRef<string | null>(null);

  useEffect(() => {
    if (!user) return;
    const updateFromPreferences = (event: Event) => {
      const detail = (event as CustomEvent<{ userId?: number }>).detail;
      if (detail?.userId !== user.id) return;
      const preferences = readPreferences(user.id);
      setMode(preferences.searchMode);
      setResultCount(preferences.resultCount);
    };
    window.addEventListener("smriti-preferences-changed", updateFromPreferences);
    return () => window.removeEventListener("smriti-preferences-changed", updateFromPreferences);
  }, [user]);

  const submitQuery = useCallback(
    async (query: string, selectedMode = mode) => {
      const trimmedQuery = query.trim();
      if (!trimmedQuery) {
        return;
      }

      const userMessage: ChatMessage = {
        id: createMessageId(),
        role: "user",
        content: trimmedQuery,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "numeric",
          minute: "2-digit",
        }),
      };

      setMessages((currentMessages) => [...currentMessages, userMessage]);
      setDraft("");
      setRetryQuery(trimmedQuery);
      setRetryMode(selectedMode);
      setIsLoading(true);

      try {
        let answer: string;
        let sources: ChatSource[];
        let noResults: boolean;
        let resultCountForHistory: number;
        if (selectedMode === "ask") {
          const accessToken = getAccessToken();
          if (!accessToken) {
            throw new ApiError("Your session has expired. Please sign in again.", 401);
          }
          const result = await postJson<RagAnswerResponse>(
            "/api/v1/search/ask",
            { query: trimmedQuery },
            accessToken,
          );
          answer = result.answer;
          sources = result.sources;
          noResults = result.status === "no_results";
          resultCountForHistory = result.sources.length;
        } else {
          const result = await workspaceRequest<RankedSearchResponse>(
            `/hybrid-search?q=${encodeURIComponent(trimmedQuery)}&limit=${resultCount}`,
          );
          sources = result.items.map(({ item, relevance_score }) =>
            toSearchSource(item, relevance_score),
          );
          noResults = sources.length === 0;
          answer = noResults
            ? "No indexed items matched that search."
            : `Found ${result.total} ranked result${result.total === 1 ? "" : "s"}.`;
          resultCountForHistory = result.total;
        }
        setMessages((currentMessages) => [
          ...currentMessages,
          {
            id: createMessageId(),
            role: "assistant",
            content: answer,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
            }),
            sources,
            noResults,
            answerMode: selectedMode,
          },
        ]);
        setHistoryError("");
        if (user && readPreferences(user.id).saveSearchHistory) {
          try {
            const sourceTypes = new Set(sources.map((source) => source.source_type));
            await createSearchHistory(trimmedQuery, selectedMode, resultCountForHistory, sourceTypes.size);
          } catch (historyFailure) {
            setHistoryError(
              historyFailure instanceof Error
                ? historyFailure.message
                : "Your answer was returned, but its search history could not be saved.",
            );
          }
        }
      } catch (error) {
        const detail = error instanceof Error ? error.message : "Please try again.";
        const message = `We couldn't complete that search. ${detail}`;

        setMessages((currentMessages) => [
          ...currentMessages,
          {
            id: createMessageId(),
            role: "assistant",
            content: message,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
            }),
            isError: true,
            retryQuery: trimmedQuery,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [mode, resultCount, user],
  );

  useEffect(() => {
    const query = searchParams.get("q");
    const requestedMode = searchParams.get("mode");
    if (requestedMode === "ask" || requestedMode === "search") {
      setMode(requestedMode);
      if (user) {
        const current = readPreferences(user.id);
        writePreferences(user.id, { ...current, searchMode: requestedMode });
      }
    }
    if (!query || handledLocationKey.current === location.key) return;
    handledLocationKey.current = location.key;
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.delete("q");
      return next;
    }, { replace: true });
    void submitQuery(
      query,
      requestedMode === "ask" || requestedMode === "search" ? requestedMode : mode,
    );
  }, [location.key, mode, searchParams, setSearchParams, submitQuery, user]);

  const onRetry = useCallback(() => {
    if (retryQuery) {
      void submitQuery(retryQuery, retryMode);
    }
  }, [retryMode, retryQuery, submitQuery]);

  const selectMode = useCallback((nextMode: "ask" | "search") => {
    setMode(nextMode);
    if (user) {
      const current = readPreferences(user.id);
      writePreferences(user.id, { ...current, searchMode: nextMode });
    }
  }, [user]);

  const pageActions = useMemo(
    () =>
      messages.length > 0 ? (
        <Button
          variant="secondary"
          className="min-h-9 border-line px-3 py-1.5 text-sm"
          onClick={() => {
            setMessages([]);
            setDraft("");
            setIsLoading(false);
            setRetryQuery(null);
          }}
        >
          New conversation
        </Button>
      ) : null,
    [messages.length],
  );

  const onSelectSuggestion = useCallback(
    (query: string) => {
      void submitQuery(query);
    },
    [submitQuery],
  );

  return (
    <div className="h-[calc(100vh-4rem)] overflow-x-hidden bg-canvas">
      {historyError && <div className="mx-auto max-w-3xl px-5 pt-4"><p className="rounded-md border border-error/30 bg-surface p-3 text-sm text-error" role="status">The answer is available, but activity could not be saved: {historyError}</p></div>}
      <ChatWindow
        draft={draft}
        isLoading={isLoading}
        mode={mode}
        messages={messages}
        onChangeMode={selectMode}
        onChangeDraft={setDraft}
        onRetry={onRetry}
        onSelectSuggestion={onSelectSuggestion}
        onSubmit={() => void submitQuery(draft)}
        pageActions={pageActions}
        reduceMotion={reduceMotion}
        suggestions={suggestedQueries}
      />
      <AnimatePresence>
        {messages.length > 0 && !isLoading && (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            className="sr-only"
            exit={{ opacity: 0, y: 12 }}
            initial={{ opacity: 0, y: 12 }}
            transition={{ duration: reduceMotion ? 0 : 0.2 }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
