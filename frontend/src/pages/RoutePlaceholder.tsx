import { Typography } from "../components/ui/Typography";

type RoutePlaceholderProps = {
  title: string;
};

export function RoutePlaceholder({ title }: RoutePlaceholderProps) {
  return (
    <section className="px-5 py-8 sm:px-8 sm:py-10 lg:px-10">
      <Typography variant="pageTitle">{title}</Typography>
      <Typography className="mt-2" variant="secondary">
        Application shell placeholder
      </Typography>
    </section>
  );
}