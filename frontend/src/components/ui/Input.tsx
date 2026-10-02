import { useId, type InputHTMLAttributes } from "react";

type InputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & {
  id?: string;
  label: string;
  error?: string;
};

export function Input({
  id,
  label,
  error,
  className = "",
  disabled,
  "aria-describedby": describedBy,
  ...props
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium text-ink" htmlFor={inputId}>
        {label}
      </label>
      <input
        id={inputId}
        className={`min-h-11 w-full rounded-md border bg-surface px-3 text-base text-ink outline-none transition-colors placeholder:text-ink-muted/70 focus:border-bronze focus-visible:ring-2 focus-visible:ring-focus-ring/30 disabled:cursor-not-allowed disabled:bg-surface-muted disabled:text-ink-muted ${error ? "border-error" : "border-line"} ${className}`}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={
          [error ? errorId : undefined, describedBy]
            .filter((value): value is string => Boolean(value))
            .join(" ") || undefined
        }
        {...props}
      />
      {error && (
        <p className="text-sm text-error" id={errorId} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}