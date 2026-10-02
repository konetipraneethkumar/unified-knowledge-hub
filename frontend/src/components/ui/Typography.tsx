import type { ElementType, HTMLAttributes } from "react";

export type TypographyVariant =
  | "pageTitle"
  | "sectionHeading"
  | "body"
  | "secondary"
  | "caption";

type TypographyProps = HTMLAttributes<HTMLElement> & {
  as?: ElementType;
  variant: TypographyVariant;
};

const tags: Record<TypographyVariant, ElementType> = {
  pageTitle: "h1",
  sectionHeading: "h2",
  body: "p",
  secondary: "p",
  caption: "span",
};

const variantClasses: Record<TypographyVariant, string> = {
  pageTitle: "text-3xl font-semibold leading-tight text-ink sm:text-4xl",
  sectionHeading: "text-xl font-semibold leading-snug text-ink",
  body: "text-base leading-7 text-ink",
  secondary: "text-sm leading-6 text-ink-muted",
  caption: "text-xs leading-5 text-ink-muted",
};

export function Typography({
  as,
  variant,
  className = "",
  ...props
}: TypographyProps) {
  const Component = as ?? tags[variant];
  return <Component className={`${variantClasses[variant]} ${className}`} {...props} />;
}