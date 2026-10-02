import type { ButtonHTMLAttributes } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-bronze text-white hover:bg-bronze-hover focus-visible:outline-focus-ring",
  secondary:
    "border border-line bg-surface text-ink hover:bg-surface-muted focus-visible:outline-focus-ring",
  ghost:
    "bg-transparent text-forest hover:bg-forest-soft focus-visible:outline-focus-ring",
};

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${variantClasses[variant]} ${className}`}
      type={type}
      {...props}
    />
  );
}