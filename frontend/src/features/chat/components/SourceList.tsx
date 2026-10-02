import type { ChatSource } from "../types";
import { SourceCard } from "./SourceCard";

type SourceListProps = {
  sources: ChatSource[];
};

export function SourceList({ sources }: SourceListProps) {
  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {sources.map((source) => (
        <SourceCard key={source.id} source={source} />
      ))}
    </div>
  );
}
