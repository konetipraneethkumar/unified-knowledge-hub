import type { ReactNode } from "react";
import { Typography } from "./Typography";

type HeaderProps = {
  actions?: ReactNode;
  className?: string;
};

export function Header({ actions, className = "" }: HeaderProps) {
  return (
    <header
      className={`flex min-h-16 items-center justify-between gap-4 border-b border-line bg-surface px-5 py-3 sm:px-8 ${className}`}
    >
      <div>
        <Typography className="text-forest" variant="sectionHeading" as="p">
          SMRITI AI
        </Typography>
        <Typography className="mt-0.5" variant="caption">
          Your digital memory.
        </Typography>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
    </header>
  );
}