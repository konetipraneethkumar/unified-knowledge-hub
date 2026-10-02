import { Typography } from "../../../components/ui/Typography";
import { SuggestedQueries } from "./SuggestedQueries";

type EmptyChatStateProps = {
  onSelectSuggestion: (query: string) => void;
  suggestions: string[];
};

export function EmptyChatState({ onSelectSuggestion, suggestions }: EmptyChatStateProps) {
  return (
    <div className="flex h-full items-center justify-center py-8">
      <div className="grid w-full max-w-2xl gap-6 rounded-2xl border border-line bg-surface p-5 sm:p-7">
        <div className="grid gap-2">
          <Typography as="h2" variant="sectionHeading">
            Search your memory
          </Typography>
          <Typography variant="secondary">
            Ask about mentors, projects, recent work, and the documents behind your knowledge graph.
          </Typography>
        </div>

        <SuggestedQueries onSelectSuggestion={onSelectSuggestion} suggestions={suggestions} />
      </div>
    </div>
  );
}
