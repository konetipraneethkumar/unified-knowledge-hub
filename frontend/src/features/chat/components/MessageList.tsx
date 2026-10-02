import { motion } from "motion/react";
import type { ChatMessage } from "../types";
import { ErrorMessage } from "./ErrorMessage";
import { MessageBubble } from "./MessageBubble";

type MessageListProps = {
  messages: ChatMessage[];
  onRetry: () => void;
  reduceMotion: boolean;
};

export function MessageList({ messages, onRetry, reduceMotion }: MessageListProps) {
  return (
    <div className="space-y-6">
      {messages.map((message) => {
        if (message.isError) {
          return (
            <motion.div
              key={message.id}
              animate={{ opacity: 1, y: 0 }}
              initial={{ opacity: 0, y: reduceMotion ? 0 : 12 }}
              transition={{ duration: reduceMotion ? 0 : 0.2, ease: "easeOut" }}
              className="flex justify-start"
            >
              <ErrorMessage
                message={message.content}
                onRetry={onRetry}
                retryQuery={message.retryQuery}
              />
            </motion.div>
          );
        }

        return (
          <MessageBubble
            key={message.id}
            message={message}
            reduceMotion={reduceMotion}
          />
        );
      })}
    </div>
  );
}
