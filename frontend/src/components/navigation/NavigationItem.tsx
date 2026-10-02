import { NavLink } from "react-router";

type NavigationItemProps = {
  label: string;
  to: string;
  onNavigate?: () => void;
};

export function NavigationItem({ label, to, onNavigate }: NavigationItemProps) {
  return (
    <NavLink
      className={({ isActive }) =>
        `group flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring ${
          isActive
            ? "bg-forest-soft text-forest"
            : "text-ink-muted hover:bg-surface-muted hover:text-ink"
        }`
      }
      end
      onClick={onNavigate}
      to={to}
    >
      {({ isActive }) => (
        <>
          <span
            aria-hidden="true"
            className={`size-2 rounded-full border ${
              isActive ? "border-forest bg-forest" : "border-ink-muted/60"
            }`}
          />
          {label}
        </>
      )}
    </NavLink>
  );
}