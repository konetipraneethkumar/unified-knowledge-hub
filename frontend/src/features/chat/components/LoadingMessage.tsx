import { Typography } from "../../../components/ui/Typography";

export function LoadingMessage() {
  return (
    <div className="flex justify-start pt-2">
      <div className="max-w-xl rounded-2xl border border-line bg-surface p-4 shadow-card">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5" aria-label="Loading">
            <span className="h-2 w-2 animate-pulse rounded-full bg-bronze [animation-delay:0ms]" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-bronze [animation-delay:120ms]" />
            <span className="h-2 w-2 animate-pulse rounded-full bg-bronze [animation-delay:240ms]" />
          </div>
          <Typography variant="secondary">Searching the local knowledge index...</Typography>
        </div>
      </div>
    </div>
  );
}
