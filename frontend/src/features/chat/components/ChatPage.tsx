import { useCallback, useMemo, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Button } from "../../../components/ui/Button";
import { suggestedQueries } from "../data/mockKnowledge";
import { resolveMockSearch } from "../services/mockSearchService";
import { ChatWindow } from "./ChatWindow";
import type { ChatMessage } from "../types";

function createMessageId() {
  return `msg-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

export function ChatPage() {
  const reduceMotion = useReducedMotion() ?? false;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [retryQuery, setRetryQuery] = useState<string | null>(null);

  const submitQuery = useCallback(
    async (query: string) => {
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
      setIsLoading(true);

      try {
        const result = await resolveMockSearch(trimmedQuery);

        setMessages((currentMessages) => [
          ...currentMessages,
          {
            id: createMessageId(),
            role: "assistant",
            content: result.answer,
            timestamp: new Date().toLocaleTimeString([], {
              hour: "numeric",
              minute: "2-digit",
            }),
            sources: result.status === "success" ? result.documents : undefined,
            isError: result.status === "error",
            retryQuery: result.status === "error" ? trimmedQuery : undefined,
          },
        ]);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Something went wrong while searching.";

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
    [],
  );

  const onRetry = useCallback(() => {
    if (retryQuery) {
      void submitQuery(retryQuery);
    }
  }, [retryQuery, submitQuery]);

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
      <ChatWindow
        draft={draft}
        isLoading={isLoading}
        messages={messages}
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
