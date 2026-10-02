import { Button } from "../../../components/ui/Button";
import { Typography } from "../../../components/ui/Typography";

type ErrorMessageProps = {
  message: string;
  onRetry?: () => void;
  retryQuery?: string;
};

export function ErrorMessage({ message, onRetry, retryQuery }: ErrorMessageProps) {
  return (
    <div className="max-w-xl rounded-2xl border border-error/30 bg-error/5 p-4 shadow-card">
      <Typography as="p" variant="body" className="text-error">
        {message}
      </Typography>

      {onRetry && (
        <div className="mt-4 flex items-center gap-3">
          <Button className="min-h-9" onClick={onRetry} type="button" variant="secondary">
            Retry
          </Button>
          {retryQuery && (
            <Typography variant="secondary" className="text-xs">
              {retryQuery}
            </Typography>
          )}
        </div>
      )}
    </div>
  );
}
