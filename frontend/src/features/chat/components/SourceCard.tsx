import { Badge } from "../../../components/ui/Badge";
import { Typography } from "../../../components/ui/Typography";
import type { ChatSource } from "../types";

export function SourceCard({ source }: { source: ChatSource }) {
  return (
    <article className="rounded-xl border border-line bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <Typography as="h3" variant="sectionHeading" className="text-base">
          {source.title}
        </Typography>
        <Badge className="shrink-0" variant="default">
          {source.type}
        </Badge>
      </div>

      <Typography className="mt-3" variant="secondary">
        {source.summary}
      </Typography>

      <div className="mt-4 flex items-center justify-between gap-3 text-xs text-ink-muted">
        <span>{source.category}</span>
        <span>{source.date}</span>
      </div>
    </article>
  );
}
