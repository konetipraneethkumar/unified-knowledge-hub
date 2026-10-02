import { useState } from "react";
import { Link } from "react-router";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Typography } from "../../components/ui/Typography";

type ConnectorStatus = "Synced" | "Connected" | "Not connected" | "Syncing";

type Connector = {
  id: string;
  name: string;
  description: string;
  status: ConnectorStatus;
};

const initialConnectors: Connector[] = [
  {
    id: "drive",
    name: "Google Drive",
    description: "Documents, presentations, and spreadsheets",
    status: "Synced",
  },
  {
    id: "gmail",
    name: "Gmail",
    description: "Messages and attachments",
    status: "Connected",
  },
  {
    id: "classroom",
    name: "Google Classroom",
    description: "Class materials and assignments",
    status: "Not connected",
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    description: "Shared conversations and files",
    status: "Not connected",
  },
  {
    id: "local",
    name: "Local Storage",
    description: "Files selected from this device",
    status: "Synced",
  },
];

const recentItems = [
  { title: "Research proposal outline", source: "Google Drive", updated: "Today, 10:42 AM" },
  { title: "Data structures lecture notes", source: "Local Storage", updated: "Yesterday" },
  { title: "Capstone project timeline", source: "Google Drive", updated: "Sep 29" },
];

const recentActivity = [
  { label: "Indexed 12 new files", detail: "Google Drive", time: "Today, 10:42 AM" },
  { label: "Searched your knowledge", detail: "Research proposal timeline", time: "Today, 9:18 AM" },
  { label: "Connected a source", detail: "Gmail", time: "Yesterday" },
];

function PageHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-8">
      <Typography variant="pageTitle">{title}</Typography>
      <Typography className="mt-2" variant="secondary">
        {subtitle}
      </Typography>
    </div>
  );
}

function PageContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-10 lg:px-10">
      {children}
    </div>
  );
}

function StatusBadge({ status }: { status: ConnectorStatus }) {
  const variant = status === "Synced" || status === "Connected" ? "success" : "default";
  const marker = status === "Synced" ? "●" : status === "Connected" ? "●" : status === "Syncing" ? "⟳" : "○";

  return (
    <Badge aria-label={`Status: ${status}`} className="gap-1.5" variant={variant}>
      <span aria-hidden="true">{marker}</span>
      {status}
    </Badge>
  );
}

export function DashboardPage() {
  const connectedCount = initialConnectors.filter(
    (connector) => connector.status === "Synced" || connector.status === "Connected",
  ).length;

  return (
    <PageContainer>
      <PageHeading title="Dashboard" subtitle="A quick view of your connected knowledge." />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <Card title="Indexed items" className="p-5">
          <p className="text-3xl font-semibold leading-tight text-ink">248</p>
          <Typography className="mt-1" variant="caption">Across your connected sources</Typography>
        </Card>
        <Card title="Connected connectors" className="p-5">
          <p className="text-3xl font-semibold leading-tight text-ink">{connectedCount}</p>
          <Typography className="mt-1" variant="caption">Of {initialConnectors.length} available sources</Typography>
        </Card>
        <Card title="Sync status" className="p-5">
          <p className="flex items-center gap-2 text-lg font-semibold text-success">
            <span aria-hidden="true">●</span> 2 Synced
          </p>
          <Typography className="mt-1" variant="caption">Most recent update today</Typography>
        </Card>
      </div>

      <div className="mb-6 flex flex-wrap gap-3">
        <Link
          className="inline-flex min-h-10 items-center justify-center rounded-md bg-bronze px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-bronze-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          to="/search"
        >
          New Query
        </Link>
        <Link
          className="inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          to="/connectors"
        >
          Connectors
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Recently indexed">
          <ul className="divide-y divide-line">
            {recentItems.map((item) => (
              <li className="flex min-w-0 items-start justify-between gap-4 py-4 first:pt-0 last:pb-0" key={item.title}>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-ink">{item.title}</p>
                  <p className="mt-1 text-xs text-ink-muted">{item.source}</p>
                </div>
                <time className="shrink-0 text-xs text-ink-muted">{item.updated}</time>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Recent activity">
          <ol className="divide-y divide-line">
            {recentActivity.map((activity) => (
              <li className="py-4 first:pt-0 last:pb-0" key={activity.label}>
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <p className="text-sm font-medium text-ink">{activity.label}</p>
                  <time className="text-xs text-ink-muted">{activity.time}</time>
                </div>
                <p className="mt-1 text-xs text-ink-muted">{activity.detail}</p>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </PageContainer>
  );
}

export function ConnectorsPage() {
  const [connectors, setConnectors] = useState(initialConnectors);

  const updateConnector = (id: string, status: ConnectorStatus) => {
    setConnectors((current) =>
      current.map((connector) => connector.id === id ? { ...connector, status } : connector),
    );
  };

  const syncConnector = (id: string) => {
    updateConnector(id, "Syncing");
    window.setTimeout(() => updateConnector(id, "Synced"), 900);
  };

  return (
    <PageContainer>
      <PageHeading title="Connectors" subtitle="Manage the sources available to your knowledge hub." />

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <Typography variant="secondary">
          {connectors.filter((connector) => connector.status !== "Not connected").length} of {connectors.length} sources connected
        </Typography>
        <Badge variant="success"><span aria-hidden="true">●</span>&nbsp; {connectors.filter((connector) => connector.status === "Synced").length} Synced</Badge>
      </div>

      <div className="grid gap-3">
        {connectors.map((connector) => {
          const isConnected = connector.status === "Connected" || connector.status === "Synced";
          const isSyncing = connector.status === "Syncing";

          return (
            <Card className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5" key={connector.id}>
              <div className="flex min-w-0 flex-1 items-start gap-4">
                <span aria-hidden="true" className="flex size-10 shrink-0 items-center justify-center rounded-md border border-line bg-surface-muted text-sm font-semibold text-forest">
                  {connector.name === "Local Storage" ? "L" : connector.name.slice(0, 1)}
                </span>
                <div className="min-w-0">
                  <h2 className="font-semibold text-ink">{connector.name}</h2>
                  <p className="mt-1 text-sm text-ink-muted">{connector.description}</p>
                  <div className="mt-2"><StatusBadge status={connector.status} /></div>
                </div>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">
                {isConnected ? (
                  <>
                    <Button disabled={isSyncing} onClick={() => syncConnector(connector.id)} variant="secondary">
                      {isSyncing ? "Syncing..." : "Sync"}
                    </Button>
                    <Button onClick={() => updateConnector(connector.id, "Not connected")} variant="ghost">
                      Disconnect
                    </Button>
                  </>
                ) : isSyncing ? (
                  <Button disabled variant="secondary">Syncing...</Button>
                ) : (
                  <Button onClick={() => updateConnector(connector.id, "Connected")}>Connect</Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </PageContainer>
  );
}

const historyEntries = [
  { kind: "Search", title: "What did we decide about the project timeline?", detail: "3 results · Google Drive, Gmail", time: "Today, 9:18 AM" },
  { kind: "Document", title: "Research proposal outline", detail: "Google Drive · Document", time: "Yesterday, 4:32 PM" },
  { kind: "Search", title: "Summarize the latest lecture notes", detail: "2 results · Local Storage", time: "Sep 29, 11:06 AM" },
  { kind: "Document", title: "Data structures lecture notes", detail: "Local Storage · PDF", time: "Sep 28, 2:14 PM" },
];

export function HistoryPage() {
  return (
    <PageContainer>
      <PageHeading title="History" subtitle="Pick up where you left off." />
      <Card className="p-0">
        <ol className="divide-y divide-line">
          {historyEntries.map((entry) => (
            <li className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:px-6" key={`${entry.kind}-${entry.title}`}>
              <div className="min-w-0">
                <div className="mb-1"><Badge>{entry.kind}</Badge></div>
                <h2 className="break-words text-sm font-medium text-ink">{entry.title}</h2>
                <p className="mt-1 text-xs text-ink-muted">{entry.detail}</p>
              </div>
              <time className="shrink-0 text-xs text-ink-muted">{entry.time}</time>
            </li>
          ))}
        </ol>
      </Card>
    </PageContainer>
  );
}

function PreferenceRow({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-line py-4 last:border-b-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
      <div>
        <h3 className="text-sm font-medium text-ink">{title}</h3>
        <p className="mt-1 text-xs leading-5 text-ink-muted">{description}</p>
      </div>
      <div className="w-full sm:w-56 sm:shrink-0">{children}</div>
    </div>
  );
}

function PreferenceSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="block">
      <span className="sr-only">{label}</span>
      <select
        aria-label={label}
        className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink outline-none focus:border-bronze focus-visible:ring-2 focus-visible:ring-focus-ring/30"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => <option key={option}>{option}</option>)}
      </select>
    </label>
  );
}

function PreferenceToggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex min-h-10 items-center gap-3 text-sm text-ink">
      <input
        aria-label={label}
        checked={checked}
        className="size-4 accent-forest"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      <span>{label}</span>
    </label>
  );
}

export function SettingsPage() {
  const [language, setLanguage] = useState("English");
  const [appearance, setAppearance] = useState("System");
  const [resultCount, setResultCount] = useState("5 results");
  const [includeAttachments, setIncludeAttachments] = useState(true);
  const [saveSearchHistory, setSaveSearchHistory] = useState(true);
  const [localFilesOnly, setLocalFilesOnly] = useState(false);

  return (
    <PageContainer>
      <PageHeading title="Settings" subtitle="Set your preferences for Smriti AI." />

      <div className="grid gap-5">
        <Card title="General">
          <PreferenceRow description="Used for dates and interface labels." title="Language">
            <PreferenceSelect label="Language" onChange={setLanguage} options={["English", "Hindi"]} value={language} />
          </PreferenceRow>
        </Card>

        <Card title="Appearance">
          <PreferenceRow description="Choose how the interface is displayed." title="Theme">
            <PreferenceSelect label="Theme" onChange={setAppearance} options={["System", "Light", "Dark"]} value={appearance} />
          </PreferenceRow>
        </Card>

        <Card title="Search preferences">
          <PreferenceRow description="Set the number of matches shown with a response." title="Results per search">
            <PreferenceSelect label="Results per search" onChange={setResultCount} options={["3 results", "5 results", "10 results"]} value={resultCount} />
          </PreferenceRow>
          <PreferenceRow description="Search text inside files attached to connected sources." title="Search attachments">
            <PreferenceToggle checked={includeAttachments} label="Include attachments" onChange={setIncludeAttachments} />
          </PreferenceRow>
        </Card>

        <Card title="Data & privacy">
          <PreferenceRow description="Keep searches in your local history view." title="Search history">
            <PreferenceToggle checked={saveSearchHistory} label="Save search history" onChange={setSaveSearchHistory} />
          </PreferenceRow>
          <PreferenceRow description="Limit search results to files stored on this device." title="Local sources only">
            <PreferenceToggle checked={localFilesOnly} label="Use local sources only" onChange={setLocalFilesOnly} />
          </PreferenceRow>
        </Card>
      </div>
    </PageContainer>
  );
}