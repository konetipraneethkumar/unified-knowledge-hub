import { NavigationItem } from "./NavigationItem";

type SidebarProps = {
  onNavigate?: () => void;
};

const navigationItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "New Query", to: "/search" },
  { label: "Connectors", to: "/connectors" },
  { label: "History", to: "/history" },
  { label: "Settings", to: "/settings" },
];

export function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <aside className="h-full min-h-[calc(100vh-4rem)] w-64 border-r border-line bg-surface px-4 py-6">
      <nav aria-label="Main navigation" className="flex flex-col gap-1">
        {navigationItems.map((item) => (
          <NavigationItem
            key={item.to}
            label={item.label}
            onNavigate={onNavigate}
            to={item.to}
          />
        ))}
      </nav>
    </aside>
  );
}