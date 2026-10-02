import { motion } from "motion/react";
import { Badge } from "../../../components/ui/Badge";
import { Typography } from "../../../components/ui/Typography";
import type { ChatMessage } from "../types";
import { SourceList } from "./SourceList";

type MessageBubbleProps = {
  message: ChatMessage;
  reduceMotion: boolean;
};

export function MessageBubble({ message, reduceMotion }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      initial={{ opacity: 0, y: reduceMotion ? 0 : 12 }}
      transition={{ duration: reduceMotion ? 0 : 0.2, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`max-w-3xl w-full ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl border p-4 shadow-card ${
            isUser
              ? "border-forest bg-forest text-white"
              : "border-line bg-surface text-ink"
          }`}
        >
          <div className="flex items-center justify-between gap-3">
            <Badge className={isUser ? "bg-white/10 text-white" : "bg-surface-muted text-ink-muted"}>
              {isUser ? "You" : "Assistant"}
            </Badge>
            <Typography
              variant="caption"
              className={isUser ? "text-white/70" : "text-ink-muted"}
            >
              {message.timestamp}
            </Typography>
          </div>

          <Typography
            as="p"
            variant="body"
            className={isUser ? "mt-3 text-white" : "mt-3 text-ink"}
          >
            {message.content}
          </Typography>

          {message.sources && message.sources.length > 0 && (
            <div className="mt-5">
              <Typography variant="secondary" className={isUser ? "text-white/80" : "text-ink-muted"}>
                Sources
              </Typography>
              <SourceList sources={message.sources} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
