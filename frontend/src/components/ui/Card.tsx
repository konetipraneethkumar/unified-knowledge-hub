import type { HTMLAttributes, ReactNode } from "react";
import { Typography } from "./Typography";

type CardProps = HTMLAttributes<HTMLElement> & {
  title?: ReactNode;
};

export function Card({ title, className = "", children, ...props }: CardProps) {
  return (
    <section
      className={`rounded-lg border border-line bg-surface p-5 shadow-card ${className}`}
      {...props}
    >
      {title && (
        <Typography className="mb-4" variant="sectionHeading" as="h2">
          {title}
        </Typography>
      )}
      {children}
    </section>
  );
}