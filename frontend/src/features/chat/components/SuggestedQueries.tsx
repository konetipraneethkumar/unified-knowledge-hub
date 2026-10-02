import { Button } from "../../../components/ui/Button";

type SuggestedQueriesProps = {
  onSelectSuggestion: (query: string) => void;
  suggestions: string[];
};

export function SuggestedQueries({ onSelectSuggestion, suggestions }: SuggestedQueriesProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {suggestions.map((suggestion) => (
        <Button
          key={suggestion}
          className="min-h-9 rounded-full border border-line bg-surface px-3 py-2 text-left text-sm font-medium text-ink hover:bg-surface-muted"
          onClick={() => onSelectSuggestion(suggestion)}
          type="button"
          variant="secondary"
        >
          {suggestion}
        </Button>
      ))}
    </div>
  );
}
