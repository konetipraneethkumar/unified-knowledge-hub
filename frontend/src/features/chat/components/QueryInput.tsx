import { Input } from "../../../components/ui/Input";

type QueryInputProps = {
  disabled?: boolean;
  isLoading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  value: string;
};

export function QueryInput({ disabled, isLoading, onChange, onSubmit, value }: QueryInputProps) {
  return (
    <form
      className="w-full"
      onSubmit={(event) => {
        event.preventDefault();
        if (!value.trim() || isLoading) {
          return;
        }
        onSubmit();
      }}
    >
      <Input
        aria-label="Search query"
        className="border-line bg-surface"
        disabled={disabled}
        label="Search query"
        onChange={(event) => onChange(event.target.value)}
        placeholder="Ask about your mentor, capstone, or retrieval work"
        value={value}
      />
    </form>
  );
}
