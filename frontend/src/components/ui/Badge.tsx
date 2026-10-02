import type { HTMLAttributes } from "react";

export type BadgeVariant = "default" | "success" | "warning";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
};

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-surface-muted text-ink-muted",
  success: "bg-forest-soft text-success",
  warning: "bg-warning-soft text-warning",
};

export function Badge({
  variant = "default",
  className = "",
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-pill px-2.5 py-1 text-xs font-medium ${variantClasses[variant]} ${className}`}
      {...props}
    />
  );
}