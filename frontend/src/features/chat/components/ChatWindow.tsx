import type { Dispatch, SetStateAction } from "react";
import { Typography } from "../../../components/ui/Typography";
import { Button } from "../../../components/ui/Button";
import { EmptyChatState } from "./EmptyChatState";
import { LoadingMessage } from "./LoadingMessage";
import { MessageList } from "./MessageList";
import { QueryInput } from "./QueryInput";
import type { ChatMessage } from "../types";

type ChatWindowProps = {
  draft: string;
  isLoading: boolean;
  messages: ChatMessage[];
  onChangeDraft: Dispatch<SetStateAction<string>>;
  onRetry: () => void;
  onSelectSuggestion: (query: string) => void;
  onSubmit: () => void;
  pageActions?: React.ReactNode;
  reduceMotion: boolean;
  suggestions: string[];
};

export function ChatWindow({
  draft,
  isLoading,
  messages,
  onChangeDraft,
  onRetry,
  onSelectSuggestion,
  onSubmit,
  pageActions,
  reduceMotion,
  suggestions,
}: ChatWindowProps) {
  return (
    <section className="mx-auto flex h-full w-full max-w-6xl flex-col px-4 py-4 sm:px-6 lg:px-8">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-line bg-surface/70 shadow-card backdrop-blur-sm">
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-4 sm:px-6">
          <div>
            <Typography as="h1" variant="pageTitle" className="text-2xl sm:text-3xl">
              New Query
            </Typography>
            <Typography className="mt-1" variant="secondary">
              Ask your knowledge base.
            </Typography>
          </div>

          {pageActions}
        </div>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-4 py-5 sm:px-6">
            {messages.length === 0 ? (
              <EmptyChatState onSelectSuggestion={onSelectSuggestion} suggestions={suggestions} />
            ) : (
              <MessageList messages={messages} onRetry={onRetry} reduceMotion={reduceMotion} />
            )}

            {isLoading && <LoadingMessage />}
          </div>

          <div className="border-t border-line bg-surface px-4 py-4 sm:px-6">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <QueryInput
                  disabled={isLoading}
                  isLoading={isLoading}
                  onChange={onChangeDraft}
                  onSubmit={onSubmit}
                  value={draft}
                />
              </div>
              <Button
                className="min-h-11 shrink-0 px-4"
                disabled={isLoading || draft.trim().length === 0}
                onClick={onSubmit}
                type="button"
              >
                {isLoading ? "Sending..." : "Send"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
