import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Typography } from "../../components/ui/Typography";
import { useAuth } from "../auth/AuthContext";
import {
  clearSearchHistory,
  listSearchHistory,
  listKnowledgePage,
  listKnowledgeItemTypes,
  listKnowledgeSources,
  listPairedDevices,
  listSyncActivity,
  readPreferences,
  writePreferences,
  workspaceRequest,
  type Connector,
  type ConnectorSyncResult,
  type KnowledgeItem,
  type PairedDevice,
  type SearchHistoryEntry,
  type SyncActivity,
  type WorkspacePreferences,
} from "./api";

function PageHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-8">
      <Typography variant="pageTitle">{title}</Typography>
      <Typography className="mt-2" variant="secondary">{subtitle}</Typography>
    </div>
  );
}

function PageContainer({ children }: { children: ReactNode }) {
  return <div className="mx-auto w-full max-w-6xl px-5 py-8 sm:px-8 sm:py-10 lg:px-10">{children}</div>;
}

function LoadError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-md border border-error/30 bg-surface p-4 text-sm text-error" role="alert">
      <p>{message}</p>
      {onRetry && <Button className="mt-3" onClick={onRetry} variant="secondary">Try again</Button>}
    </div>
  );
}

function LoadingMessage() {
  return <p aria-live="polite" className="py-8 text-sm text-ink-muted">Loading your data…</p>;
}

function EmptyMessage({ children }: { children: ReactNode }) {
  return <p className="py-6 text-sm text-ink-muted">{children}</p>;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Not available"
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function itemTitle(item: KnowledgeItem) {
  return item.title?.trim() || item.location?.trim() || "Untitled indexed item";
}

function connectorName(connector: Connector) {
  if (connector.name.trim()) return connector.name;
  return connector.connector_type.replaceAll("_", " ");
}

function activeConnectors(connectors: Connector[]) {
  return connectors.filter((connector) => !connector.revoked_at && connector.status !== "revoked");
}

function connectorState(connector: Connector) {
  if (connector.status === "syncing") return "Syncing";
  if (connector.status === "error") return "Sync failed";
  if (connector.status === "revoked" || connector.authentication_status === "revoked") return "Not connected";
  return connector.last_sync_at ? "Synced" : "Connected";
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [totalItems, setTotalItems] = useState<number | null>(null);
  const [searches, setSearches] = useState<SearchHistoryEntry[]>([]);
  const [syncActivity, setSyncActivity] = useState<SyncActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [quickQuery, setQuickQuery] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [knowledge, count, sources, history, activity] = await Promise.all([
        workspaceRequest<KnowledgeItem[]>("/knowledge-items/recent?limit=5"),
        workspaceRequest<{ total: number }>("/knowledge-items/count"),
        workspaceRequest<Connector[]>("/connectors"),
        listSearchHistory(),
        listSyncActivity(),
      ]);
      setItems(knowledge);
      setTotalItems(count.total);
      setConnectors(sources);
      setSearches(history.slice(0, 5));
      setSyncActivity(activity.slice(0, 5));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load your dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadDashboard(); }, [loadDashboard]);

  const supportedTypes = new Set(["LOCAL", "GOOGLE_DRIVE", "GMAIL", "GOOGLE_CLASSROOM"]);
  const connected = activeConnectors(connectors).filter((connector) => supportedTypes.has(connector.connector_type));
  const synced = connected.filter((connector) => connector.last_sync_at);
  const recentItems = items;
  const latestSync = synced.length
    ? new Date(Math.max(...synced.map((connector) => new Date(connector.last_sync_at!).getTime()))).toISOString()
    : null;

  return (
    <PageContainer>
      <PageHeading
        title={user?.display_name ? `Welcome, ${user.display_name}` : "Dashboard"}
        subtitle="A live overview of your indexed knowledge and connected sources."
      />
      {error && <div className="mb-5"><LoadError message={error} onRetry={() => void loadDashboard()} /></div>}
      <form className="mb-6 flex flex-col gap-3 rounded-xl border border-line bg-surface p-4 shadow-card sm:flex-row sm:p-5" onSubmit={(event) => {
        event.preventDefault();
        const query = quickQuery.trim();
        if (query) navigate(`/search?q=${encodeURIComponent(query)}`);
      }}>
        <label className="sr-only" htmlFor="dashboard-quick-ask">Ask a question about your indexed knowledge</label>
        <input className="min-h-11 min-w-0 flex-1 rounded-md border border-line bg-canvas px-3 text-sm text-ink outline-none focus:border-bronze focus-visible:ring-2 focus-visible:ring-focus-ring/30" id="dashboard-quick-ask" onChange={(event) => setQuickQuery(event.target.value)} placeholder="Ask something from your indexed knowledge…" value={quickQuery} />
        <Button disabled={!quickQuery.trim()} type="submit">Ask SMRITI</Button>
      </form>
      {loading ? <LoadingMessage /> : error ? null : <>
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <Card title="Indexed items" className="p-5">
            <p className="text-3xl font-semibold leading-tight text-ink">{totalItems ?? "—"}</p>
            <Typography className="mt-1" variant="caption">Indexed items in your account</Typography>
          </Card>
          <Card title="Connected sources" className="p-5">
            <p className="text-3xl font-semibold leading-tight text-ink">{connected.length}</p>
            <Typography className="mt-1" variant="caption">Active connectors on your account</Typography>
          </Card>
          <Card title="Sources synced" className="p-5">
            <p className="text-3xl font-semibold leading-tight text-ink">{synced.length}</p>
            <Typography className="mt-1" variant="caption">
              {latestSync ? `Latest: ${formatDate(latestSync)}` : "No completed sync is recorded yet"}
            </Typography>
          </Card>
        </div>
        <div className="mb-6 flex flex-wrap gap-3">
          <Link className="inline-flex min-h-10 items-center justify-center rounded-md bg-bronze px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-bronze-hover" to="/search">Ask your knowledge</Link>
          <Link className="inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink hover:bg-surface-muted" to="/knowledge">Browse knowledge</Link>
          <Link className="inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink hover:bg-surface-muted" to="/connectors">Manage sources</Link>
          <Link className="inline-flex min-h-10 items-center justify-center rounded-md border border-line bg-surface px-4 py-2 text-sm font-medium text-ink hover:bg-surface-muted" to="/history">View history</Link>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Connected sources">
            {connected.length ? <ul className="divide-y divide-line">
              {connected.map((connector) => <li className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0 last:pb-0" key={connector.id}>
                <div><p className="text-sm font-medium text-ink">{connectorName(connector)}</p><p className="mt-1 text-xs text-ink-muted">{connector.indexed_item_count ?? "Not available"} indexed items</p></div>
                <Badge variant={connector.status === "error" ? "warning" : "default"}>{connectorState(connector)}</Badge>
              </li>)}
            </ul> : <EmptyMessage>No supported sources are connected to this account yet.</EmptyMessage>}
          </Card>
          <Card title="Recently indexed">
            {recentItems.length ? <ul className="divide-y divide-line">
              {recentItems.map((item) => <li className="flex min-w-0 items-start justify-between gap-4 py-4 first:pt-0 last:pb-0" key={item.id}>
                <div className="min-w-0"><p className="truncate text-sm font-medium text-ink">{itemTitle(item)}</p><p className="mt-1 text-xs text-ink-muted">{item.source.replaceAll("_", " ")}</p></div>
                <time className="shrink-0 text-xs text-ink-muted">{formatDate(item.modified_at || item.indexed_at)}</time>
              </li>)}
            </ul> : <EmptyMessage>No knowledge items have been indexed for this account yet.</EmptyMessage>}
          </Card>
          <Card title="Recent synchronization">
            {syncActivity.length ? <ol className="divide-y divide-line">
              {syncActivity.map((activity) => <li className="py-4 first:pt-0 last:pb-0" key={activity.id}>
                <div className="flex flex-wrap items-baseline justify-between gap-2"><p className="text-sm font-medium text-ink">{activity.connector_name}</p><time className="text-xs text-ink-muted">{formatDate(activity.created_at)}</time></div>
                <p className="mt-1 text-xs text-ink-muted">{activity.status.replaceAll("_", " ")} · {activity.processed ?? "—"} processed · {activity.skipped ?? "—"} skipped · {activity.failed ?? "—"} failed · {activity.deleted ?? "—"} deleted</p>
              </li>)}
            </ol> : <EmptyMessage>No sync timestamps are available yet. Connectors report their latest sync status on the Connectors page.</EmptyMessage>}
          </Card>
          <Card title="Recent searches">
            {searches.length ? <ol className="divide-y divide-line">
              {searches.map((entry) => <li className="flex flex-wrap items-center justify-between gap-3 py-4 first:pt-0 last:pb-0" key={entry.id}>
                <div className="min-w-0"><p className="truncate text-sm font-medium text-ink">{entry.query}</p><p className="mt-1 text-xs text-ink-muted">{entry.result_count} results · {entry.source_count} source types</p></div>
                <Link className="shrink-0 text-sm font-medium text-forest underline-offset-4 hover:underline" to={`/search?q=${encodeURIComponent(entry.query)}&mode=${entry.mode}`}>{entry.mode === "ask" ? "Ask again" : "Search again"}</Link>
              </li>)}
            </ol> : <EmptyMessage>Your completed searches appear here when search history is enabled.</EmptyMessage>}
          </Card>
        </div>
      </>}
    </PageContainer>
  );
}

type ConnectorCatalogEntry = { kind: string; type: string; name: string; description: string };
const googleConnectorCatalog: ConnectorCatalogEntry[] = [
  { kind: "google-drive", type: "GOOGLE_DRIVE", name: "Google Drive", description: "Documents, presentations, and spreadsheets" },
  { kind: "gmail", type: "GMAIL", name: "Gmail", description: "Messages and attachments" },
  { kind: "google-classroom", type: "GOOGLE_CLASSROOM", name: "Google Classroom", description: "Courses and shared class materials" },
];

export function ConnectorsPage() {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [devices, setDevices] = useState<PairedDevice[]>([]);
  const [localName, setLocalName] = useState("");
  const [localDeviceId, setLocalDeviceId] = useState("");
  const [localFolder, setLocalFolder] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyConnector, setBusyConnector] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<ConnectorSyncResult | null>(null);
  const [syncFailure, setSyncFailure] = useState<{ connector: Connector; message: string } | null>(null);

  const loadConnectors = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [connected, pairedDevices] = await Promise.all([
        workspaceRequest<Connector[]>("/connectors"),
        listPairedDevices(),
      ]);
      setConnectors(connected);
      setDevices(pairedDevices.filter((device) => !device.revoked_at));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load your connectors.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadConnectors(); }, [loadConnectors]);

  const connectGoogle = async (kind: string) => {
    setBusyConnector(kind);
    setActionError("");
    try {
      const { url } = await workspaceRequest<{ url: string }>(`/api/v1/connectors/${kind}/connect-url`);
      window.location.assign(url);
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : `Could not connect ${kind}.`);
      setBusyConnector(null);
    }
  };

  const connectLocal = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusyConnector("LOCAL");
    setActionError("");
    setNotice("");
    try {
      await workspaceRequest<Connector>("/connectors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          connector_type: "LOCAL",
          name: localName.trim(),
          device_id: localDeviceId,
          authorized_root: localFolder.trim(),
        }),
      });
      setLocalName("");
      setLocalFolder("");
      setNotice("Local source connected. Initial indexing has started.");
      await loadConnectors();
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : "Could not connect this local source.");
    } finally {
      setBusyConnector(null);
    }
  };

  const syncConnector = async (connector: Connector) => {
    setBusyConnector(connector.id);
    setError("");
    setActionError("");
    setNotice("");
    setLastSync(null);
    setSyncFailure(null);
    try {
      const result = await workspaceRequest<ConnectorSyncResult>(`/api/v1/connectors/${encodeURIComponent(connector.id)}/sync`, { method: "POST" });
      setLastSync(result);
      await loadConnectors();
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Please try syncing again.";
      setSyncFailure({ connector, message });
    } finally {
      setBusyConnector(null);
    }
  };

  const disconnectConnector = async (connector: Connector, googleKind?: string) => {
    if (!window.confirm(`Disconnect ${connectorName(connector)}? Existing indexed knowledge will remain available.`)) return;
    setBusyConnector(connector.id);
    setActionError("");
    try {
      const path = googleKind
        ? `/api/v1/connectors/${googleKind}/disconnect`
        : `/connectors/${encodeURIComponent(connector.id)}`;
      await workspaceRequest<void>(path, { method: googleKind ? "POST" : "DELETE" });
      setNotice(`${connectorName(connector)} disconnected.`);
      await loadConnectors();
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : `Could not disconnect ${connectorName(connector)}.`);
    } finally {
      setBusyConnector(null);
    }
  };

  const currentConnectors = activeConnectors(connectors);
  const supportedTypes = new Set(["LOCAL", ...googleConnectorCatalog.map((entry) => entry.type)]);
  const supportedConnectors = currentConnectors.filter((connector) => supportedTypes.has(connector.connector_type));
  const googleConnectors = googleConnectorCatalog.map((entry) => ({
    ...entry,
    connector: currentConnectors.find((candidate) => candidate.connector_type === entry.type),
  }));
  const localConnector = supportedConnectors.find((connector) => connector.connector_type === "LOCAL");

  return (
    <PageContainer>
      <PageHeading title="Connectors" subtitle="Manage the sources currently linked to your account and inspect their sync state." />
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <Typography variant="secondary">{supportedConnectors.length} connected source{supportedConnectors.length === 1 ? "" : "s"}</Typography>
        <Link className="text-sm font-medium text-forest underline-offset-4 hover:underline" to="/history?tab=sync">View sync activity</Link>
      </div>
      {error && <div className="mb-4"><LoadError message={error} /></div>}
      {actionError && <div className="mb-4"><LoadError message={actionError} /></div>}
      {notice && <p className="mb-4 text-sm text-success" role="status">{notice}</p>}
      {lastSync && <Card className="mb-4 p-4" title="Sync result">
        <p aria-live="polite" className={lastSync.failed ? "text-sm text-warning" : "text-sm text-success"}>{lastSync.status.replaceAll("_", " ")} · {lastSync.processed} processed · {lastSync.skipped} skipped · {lastSync.failed} failed · {lastSync.deleted} removed</p>
        {!!lastSync.errors.length && <ul className="mt-2 list-disc pl-5 text-sm text-error">{lastSync.errors.map((message, index) => <li key={`${index}-${message}`}>{message}</li>)}</ul>}
      </Card>}
      {syncFailure && <Card className="mb-4 border-error/30 p-4" title={`${connectorName(syncFailure.connector)} sync failed`}>
        <p className="text-sm text-error">{connectorName(syncFailure.connector)} sync failed. Your existing indexed knowledge is still available. {syncFailure.message}</p>
        <Button className="mt-3" disabled={busyConnector === syncFailure.connector.id} onClick={() => void syncConnector(syncFailure.connector)} variant="secondary">{busyConnector === syncFailure.connector.id ? "Syncing…" : "Retry sync"}</Button>
      </Card>}
      {!loading && !error && supportedConnectors.length === 0 && <p className="mb-4 text-sm text-ink-muted">Connect your first source to start building your knowledge index.</p>}
      {loading ? <LoadingMessage /> : error ? null : <div className="grid gap-3">
        {googleConnectors.map(({ kind, name, description, connector }) => <Card className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5" key={kind}>
          <div className="flex min-w-0 flex-1 items-start gap-4">
            <span aria-hidden="true" className="flex size-10 shrink-0 items-center justify-center rounded-md border border-line bg-surface-muted text-sm font-semibold text-forest">G</span>
            <div className="min-w-0"><h2 className="font-semibold text-ink">{name}</h2><p className="mt-1 text-sm text-ink-muted">{description}</p>
              <div className="mt-2"><Badge variant={connector?.status === "error" ? "warning" : connector ? "success" : "default"}>{connector ? (connector.status === "error" ? "Sync failed" : busyConnector === connector.id ? "Syncing" : "Connected") : "Not connected"}</Badge>{connector?.last_sync_at && <Badge className="ml-2" variant="default">Last synced {formatDate(connector.last_sync_at)}</Badge>}</div>
              {connector && <p className="mt-2 text-xs text-ink-muted">Indexed items: {connector.indexed_item_count ?? "Not available"} · Last sync: {formatDate(connector.last_sync_at)}</p>}
              {connector?.external_account_id && <p className="mt-1 text-xs text-ink-muted">Account: {connector.external_account_id}</p>}
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">
            {connector ? <>
              <Button disabled={busyConnector === connector.id} onClick={() => void syncConnector(connector)} variant="secondary">{busyConnector === connector.id ? "Working…" : "Sync now"}</Button>
              <Button disabled={busyConnector === connector.id} onClick={() => void disconnectConnector(connector, kind)} variant="ghost">Disconnect</Button>
            </> : <Button disabled={busyConnector === kind} onClick={() => void connectGoogle(kind)} variant="secondary">{busyConnector === kind ? "Opening…" : "Connect"}</Button>}
          </div>
          {connector && <details className="basis-full border-t border-line pt-3 text-sm">
            <summary className="cursor-pointer font-medium text-forest">Manage details</summary>
            <dl className="mt-3 grid gap-2 text-xs text-ink-muted sm:grid-cols-2">
              <div><dt className="font-medium text-ink">Connection</dt><dd>{connector.authentication_status.replaceAll("_", " ")}</dd></div>
              <div><dt className="font-medium text-ink">Last successful sync</dt><dd>{formatDate(connector.last_sync_at)}</dd></div>
            </dl>
          </details>}
        </Card>)}
        <Card className="p-4 sm:p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div><h2 className="font-semibold text-ink">Local folder</h2><p className="mt-1 text-sm text-ink-muted">Index a folder available to your paired SMRITI device. Source files remain where they are.</p></div>
            {localConnector
              ? <><Badge variant={localConnector.status === "error" ? "warning" : "success"}>{localConnector.status === "error" ? "Sync failed" : busyConnector === localConnector.id ? "Syncing" : "Connected"}</Badge>{localConnector.last_sync_at && <Badge>Last synced {formatDate(localConnector.last_sync_at)}</Badge>}</>
              : <Badge>Not connected</Badge>}
          </div>
          {localConnector ? <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
            <div><p className="text-sm text-ink">{localConnector.indexed_item_count ?? "Not available"} indexed items</p><p className="mt-1 break-all text-xs text-ink-muted">{localConnector.authorized_root || "Location unavailable"}</p></div>
            <div className="flex flex-wrap gap-2">
              <Button disabled={busyConnector === localConnector.id} onClick={() => void syncConnector(localConnector)} variant="secondary">{busyConnector === localConnector.id ? "Syncing…" : "Sync now"}</Button>
              <Button disabled={busyConnector === localConnector.id} onClick={() => void disconnectConnector(localConnector)} variant="ghost">Disconnect</Button>
            </div>
          </div> : <form className="mt-4 grid gap-3 border-t border-line pt-4 sm:grid-cols-2" onSubmit={(event) => void connectLocal(event)}>
            {devices.length ? <>
              <label className="grid gap-1 text-sm font-medium text-ink" htmlFor="local-source-name">Source name<input className="min-h-10 rounded-md border border-line bg-surface px-3 font-normal" id="local-source-name" maxLength={120} onChange={(event) => setLocalName(event.target.value)} required value={localName} /></label>
              <label className="grid gap-1 text-sm font-medium text-ink" htmlFor="local-device">Paired device<select className="min-h-10 rounded-md border border-line bg-surface px-3 font-normal" id="local-device" onChange={(event) => setLocalDeviceId(event.target.value)} required value={localDeviceId}><option value="">Select a device</option>{devices.map((device) => <option key={device.id} value={device.id}>{device.name}</option>)}</select></label>
              <label className="grid gap-1 text-sm font-medium text-ink sm:col-span-2" htmlFor="local-folder">Authorized folder path<input className="min-h-10 rounded-md border border-line bg-surface px-3 font-normal" id="local-folder" onChange={(event) => setLocalFolder(event.target.value)} placeholder="Folder path under the server's configured local storage root" required value={localFolder} /></label>
              <p className="text-xs leading-5 text-ink-muted sm:col-span-2">Enter a folder path that the backend administrator has placed under the configured local-storage root. Paths outside that root will be rejected.</p>
              <div className="sm:col-span-2"><Button disabled={busyConnector === "LOCAL" || !localDeviceId || !localName.trim() || !localFolder.trim()} type="submit">{busyConnector === "LOCAL" ? "Connecting…" : "Connect local folder"}</Button></div>
            </> : <p className="text-sm text-ink-muted sm:col-span-2">Pair a device with the SMRITI desktop client before connecting a local folder. This web app will not read files directly from your browser.</p>}
          </form>}
        </Card>
      </div>}
      <p className="mt-5 text-xs leading-5 text-ink-muted">Supported connectors are Google Drive, Gmail, Google Classroom, and a paired-device local folder. Other connector types are not shown as active.</p>
    </PageContainer>
  );
}

function SearchHistoryPanel() {
  const [entries, setEntries] = useState<SearchHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [cleared, setCleared] = useState(false);

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setEntries(await listSearchHistory());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load search history.");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void loadHistory(); }, [loadHistory]);

  const clearHistory = async () => {
    setBusy(true);
    setError("");
    try {
      await clearSearchHistory();
      setEntries([]);
      setCleared(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not clear search history.");
    } finally {
      setBusy(false);
    }
  };

  return <Card className="p-0">
    <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-4 sm:px-6">
      <div><h2 className="text-sm font-semibold text-ink">Recent questions</h2><p className="mt-1 text-xs text-ink-muted">Search history saved to your authenticated account.</p></div>
      {entries.length > 0 && <Button disabled={busy} onClick={() => void clearHistory()} variant="ghost">{busy ? "Clearing…" : "Clear history"}</Button>}
    </div>
    {error && <div className="p-5"><LoadError message={error} onRetry={() => void loadHistory()} /></div>}
    {loading ? <div className="px-5 sm:px-6"><LoadingMessage /></div> : entries.length ? <ol className="divide-y divide-line">
      {entries.map((entry) => <li className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:px-6" key={entry.id}>
        <div className="min-w-0"><div className="mb-1"><Badge>{entry.mode === "ask" ? "Ask" : "Search"}</Badge></div><h3 className="break-words text-sm font-medium text-ink">{entry.query}</h3><p className="mt-1 text-xs text-ink-muted">{entry.result_count} results · {entry.source_count} source types</p></div>
          <div className="flex shrink-0 items-center gap-4"><time className="text-xs text-ink-muted">{formatDate(entry.created_at)}</time><Link className="text-sm font-medium text-forest underline-offset-4 hover:underline" to={`/search?q=${encodeURIComponent(entry.query)}&mode=${entry.mode}`}>{entry.mode === "ask" ? "Ask again" : "Search again"}</Link></div>
      </li>)}
    </ol> : !error && <div className="px-5 py-2 sm:px-6"><EmptyMessage>{cleared ? "Your search history is clear." : "Your completed searches appear here when search history is enabled in Settings."}</EmptyMessage></div>}
  </Card>;
}

function SyncActivityPanel() {
  const [activity, setActivity] = useState<SyncActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadActivity = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setActivity(await listSyncActivity()); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load connector activity."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void loadActivity(); }, [loadActivity]);
  if (loading) return <LoadingMessage />;
  if (error) return <LoadError message={error} onRetry={() => void loadActivity()} />;
  return <Card className="p-0">
    <div className="border-b border-line px-5 py-4 sm:px-6"><h2 className="text-sm font-semibold text-ink">Synchronization events</h2><p className="mt-1 text-xs text-ink-muted">Each event reports actual connector processing results.</p></div>
    {activity.length ? <ol className="divide-y divide-line">
      {activity.map((entry) => <li className="flex flex-col gap-2 px-5 py-4 sm:px-6" key={entry.id}>
        <div className="flex flex-wrap items-center justify-between gap-3">
            <div><div className="mb-1"><Badge variant={entry.failed || entry.status === "failed" ? "warning" : "default"}>{entry.status.replaceAll("_", " ")}</Badge></div><h3 className="text-sm font-medium text-ink">{entry.connector_name}</h3><p className="mt-1 text-xs text-ink-muted">{entry.connector_type.replaceAll("_", " ")}</p></div>
          <time className="text-xs text-ink-muted">{formatDate(entry.created_at)}</time>
        </div>
        <p className="text-xs text-ink-muted">{entry.processed ?? "—"} processed · {entry.skipped ?? "—"} skipped · {entry.failed ?? "—"} failed · {entry.deleted ?? "—"} deleted</p>
      </li>)}
    </ol> : <div className="px-5 py-2 sm:px-6"><EmptyMessage>No synchronization events have been recorded for this account.</EmptyMessage></div>}
  </Card>;
}

export function HistoryPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<"search" | "sync">(() => new URLSearchParams(window.location.search).get("tab") === "sync" ? "sync" : "search");
  useEffect(() => {
    const onPopState = () => setTab(new URLSearchParams(window.location.search).get("tab") === "sync" ? "sync" : "search");
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);
  const selectTab = (value: "search" | "sync") => {
    setTab(value);
    const url = new URL(window.location.href);
    if (value === "sync") url.searchParams.set("tab", "sync");
    else url.searchParams.delete("tab");
    window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
  };
  if (!user) return null;
  return <PageContainer>
    <PageHeading title="History" subtitle="Review questions asked and the latest sync state reported by your sources." />
    <div className="mb-5 flex gap-2 border-b border-line" role="tablist" aria-label="History views">
      <button aria-selected={tab === "search"} className={`border-b-2 px-4 py-3 text-sm font-medium ${tab === "search" ? "border-bronze text-ink" : "border-transparent text-ink-muted"}`} onClick={() => selectTab("search")} role="tab" type="button">Search history</button>
      <button aria-selected={tab === "sync"} className={`border-b-2 px-4 py-3 text-sm font-medium ${tab === "sync" ? "border-bronze text-ink" : "border-transparent text-ink-muted"}`} onClick={() => selectTab("sync")} role="tab" type="button">Sync activity</button>
    </div>
    {tab === "search" ? <SearchHistoryPanel /> : <SyncActivityPanel />}
  </PageContainer>;
}

export function KnowledgePage() {
  const { user } = useAuth();
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [total, setTotal] = useState(0);
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("All sources");
  const [itemType, setItemType] = useState("All types");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [itemTypes, setItemTypes] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(() => user ? readPreferences(user.id).knowledgePageSize : 20);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [result, sourceList, typeList] = await Promise.all([
        listKnowledgePage({
          offset: page * pageSize,
          limit: pageSize,
          query,
          source: source === "All sources" ? "" : source,
          itemType: itemType === "All types" ? "" : itemType,
          dateFrom,
          dateTo,
        }),
        listKnowledgeSources(),
        listKnowledgeItemTypes(),
      ]);
      setItems(result.items);
      setTotal(result.total);
      setSources(sourceList);
      setItemTypes(typeList);
    }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load your knowledge library."); }
    finally { setLoading(false); }
  }, [dateFrom, dateTo, itemType, page, pageSize, query, source]);
  useEffect(() => { void loadItems(); }, [loadItems]);
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  const changePageSize = (value: number) => {
    setPageSize(value);
    if (user) writePreferences(user.id, { ...readPreferences(user.id), knowledgePageSize: value });
  };

  return <PageContainer>
    <PageHeading title="Knowledge" subtitle="Browse the index of source items SMRITI can search. Original files remain in their source locations." />
    <Card className="mb-5 p-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <label className="block"><span className="sr-only">Filter knowledge</span><input className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm outline-none focus:border-bronze focus-visible:ring-2 focus-visible:ring-focus-ring/30" onChange={(event) => { setPage(0); setQuery(event.target.value); }} placeholder="Filter titles, summaries, and sources…" value={query} /></label>
        <label className="block"><span className="sr-only">Filter by source</span><select className="min-h-10 rounded-md border border-line bg-surface px-3 text-sm" onChange={(event) => { setPage(0); setSource(event.target.value); }} value={source}><option>All sources</option>{sources.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
        <label className="block"><span className="sr-only">Filter by item type</span><select className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm" onChange={(event) => { setPage(0); setItemType(event.target.value); }} value={itemType}><option>All types</option>{itemTypes.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select></label>
        <label className="flex items-center gap-2 text-xs text-ink-muted"><span className="shrink-0">From</span><input aria-label="Date from" className="min-h-10 min-w-0 flex-1 rounded-md border border-line bg-surface px-2 text-sm text-ink" onChange={(event) => { setPage(0); setDateFrom(event.target.value); }} type="date" value={dateFrom} /></label>
        <label className="flex items-center gap-2 text-xs text-ink-muted"><span className="shrink-0">To</span><input aria-label="Date to" className="min-h-10 min-w-0 flex-1 rounded-md border border-line bg-surface px-2 text-sm text-ink" onChange={(event) => { setPage(0); setDateTo(event.target.value); }} type="date" value={dateTo} /></label>
        <label className="flex items-center gap-2 text-xs text-ink-muted"><span>Page size</span><select className="min-h-10 rounded-md border border-line bg-surface px-2 text-sm text-ink" onChange={(event) => { setPage(0); changePageSize(Number(event.target.value)); }} value={pageSize}><option value={10}>10</option><option value={20}>20</option><option value={50}>50</option></select></label>
      </div>
    </Card>
    {error && <div className="mb-4"><LoadError message={error} onRetry={() => void loadItems()} /></div>}
    {loading ? <LoadingMessage /> : error ? null : <>
      <div className="mb-3 flex items-center justify-between gap-4"><Typography variant="secondary">{total} item{total === 1 ? "" : "s"}</Typography>{total > 0 && <span className="text-xs text-ink-muted">Showing {page * pageSize + 1}–{page * pageSize + items.length} of {total}</span>}</div>
      <div className="grid gap-3">
        {items.map((item) => <Card className="p-4 sm:p-5" key={item.id}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0"><h2 className="break-words font-semibold text-ink">{itemTitle(item)}</h2><p className="mt-1 text-sm text-ink-muted">{item.source.replaceAll("_", " ")}{item.item_type ? ` · ${item.item_type.replaceAll("_", " ")}` : ""}</p></div>
            <Badge variant={item.processing_status === "failed" ? "warning" : "default"}>{item.processing_status.replaceAll("_", " ")}</Badge>
          </div>
          {item.summary && <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-ink-muted">{item.summary}</p>}
          {item.processing_error && <p className="mt-2 text-sm text-error">{item.processing_error}</p>}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-3 text-xs text-ink-muted">
            <span>{item.file_path || item.location || "Location unavailable"}</span>
            <div className="flex gap-3"><span>Indexed {formatDate(item.indexed_at)}</span>{item.web_url && <a className="font-medium text-forest underline-offset-4 hover:underline" href={item.web_url} rel="noreferrer" target="_blank">Open source</a>}</div>
          </div>
          <details className="mt-3 border-t border-line pt-3 text-sm">
            <summary className="cursor-pointer font-medium text-forest">Item details</summary>
            <dl className="mt-3 grid gap-x-5 gap-y-3 sm:grid-cols-2">
              <div><dt className="text-xs text-ink-muted">Source type</dt><dd className="mt-1 text-ink">{item.source.replaceAll("_", " ")}</dd></div>
              <div><dt className="text-xs text-ink-muted">Item type</dt><dd className="mt-1 text-ink">{item.item_type || item.mime_type || "Not available"}</dd></div>
                    <div><dt className="text-xs text-ink-muted">Last modified</dt><dd className="mt-1 text-ink">{formatDate(item.modified_at)}</dd></div>
              <div><dt className="text-xs text-ink-muted">Indexed</dt><dd className="mt-1 text-ink">{formatDate(item.indexed_at)}</dd></div>
              <div className="sm:col-span-2"><dt className="text-xs text-ink-muted">Provenance</dt><dd className="mt-1 break-all text-ink">{item.parent_location || item.file_path || item.location || "Location unavailable"}</dd></div>
            </dl>
          </details>
        </Card>)}
        {!items.length && <Card><EmptyMessage>{total ? "No items are present on this page." : (query || source !== "All sources" || itemType !== "All types" || dateFrom || dateTo) ? "No indexed items match these filters." : "No knowledge has been indexed yet. Connect and sync a source to start building your index."}</EmptyMessage></Card>}
      </div>
      {total > pageSize && <div className="mt-5 flex items-center justify-between"><Button disabled={page === 0} onClick={() => setPage((current) => Math.max(0, current - 1))} variant="secondary">Previous</Button><span className="text-sm text-ink-muted">Page {page + 1} of {pageCount}</span><Button disabled={page + 1 >= pageCount} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))} variant="secondary">Next</Button></div>}
    </>}
  </PageContainer>;
}

function PreferenceRow({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return <div className="flex flex-col gap-3 border-b border-line py-4 last:border-b-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between sm:gap-6"><div><h3 className="text-sm font-medium text-ink">{title}</h3><p className="mt-1 text-xs leading-5 text-ink-muted">{description}</p></div><div className="w-full sm:w-56 sm:shrink-0">{children}</div></div>;
}

export function SettingsPage() {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState<WorkspacePreferences>(() => user ? readPreferences(user.id) : readPreferences(-1));
  const [saved, setSaved] = useState(false);
  const [settingsError, setSettingsError] = useState("");
  const [clearingHistory, setClearingHistory] = useState(false);
  useEffect(() => {
    if (user) setPreferences(readPreferences(user.id));
  }, [user]);
  const updatePreferences = (next: WorkspacePreferences) => {
    setSettingsError("");
    setSaved(false);
    try {
      if (user) writePreferences(user.id, next);
      setPreferences(next);
      setSaved(true);
    } catch (cause) {
      setSettingsError(cause instanceof Error ? cause.message : "Could not save this browser preference.");
    }
  };
  const clearHistory = async () => {
    if (!window.confirm("Permanently clear your saved search history?")) return;
    setClearingHistory(true);
    setSettingsError("");
    try {
      await clearSearchHistory();
      setSaved(true);
    } catch (cause) {
      setSettingsError(cause instanceof Error ? cause.message : "Could not clear search history.");
    } finally {
      setClearingHistory(false);
    }
  };
  return <PageContainer>
    <PageHeading title="Settings" subtitle="Manage preferences that are currently supported by your account and this application." />
    <div className="grid gap-5">
      <Card title="Account">
        <PreferenceRow description="Profile details are supplied by your authenticated account. Password and security changes are not available in this application yet." title="Profile">
          <Link className="inline-flex min-h-10 items-center font-medium text-forest underline-offset-4 hover:underline" to="/profile">View profile</Link>
        </PreferenceRow>
      </Card>
      <Card title="Search & AI">
        <PreferenceRow description="Choose whether Search opens in grounded answer mode or ranked retrieval mode. You can still switch modes on the Search page." title="Default search mode">
          <select aria-label="Default search mode" className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink" onChange={(event) => updatePreferences({ ...preferences, searchMode: event.target.value as WorkspacePreferences["searchMode"] })} value={preferences.searchMode}><option value="ask">Ask with an answer</option><option value="search">Ranked results</option></select>
        </PreferenceRow>
        <PreferenceRow description="Number of ranked results requested from the hybrid retrieval API. Ask mode uses the server-configured context limit." title="Ranked result count">
          <select aria-label="Ranked result count" className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink" onChange={(event) => updatePreferences({ ...preferences, resultCount: Number(event.target.value) })} value={preferences.resultCount}><option value={5}>5 results</option><option value={10}>10 results</option><option value={20}>20 results</option></select>
        </PreferenceRow>
        <PreferenceRow description="Show the source summary or evidence returned by retrieval alongside source details." title="Show evidence and summaries">
          <label className="flex min-h-10 items-center gap-3 text-sm text-ink"><input aria-label="Show evidence and summaries" checked={preferences.showEvidence} className="size-4 accent-forest" onChange={(event) => updatePreferences({ ...preferences, showEvidence: event.target.checked })} type="checkbox" /><span>{preferences.showEvidence ? "Enabled" : "Disabled"}</span></label>
        </PreferenceRow>
        <p className="mt-3 text-sm leading-6 text-ink-muted">AI answer generation and context size are server-controlled; the backend does not expose per-user overrides.</p>
      </Card>
      <Card title="Sources & Sync">
        <p className="text-sm leading-6 text-ink-muted">Source connections and manual synchronization are managed on the Connectors page. The current API does not expose global sync schedules or notification preferences.</p>
        <Link className="mt-3 inline-flex min-h-10 items-center font-medium text-forest underline-offset-4 hover:underline" to="/connectors">Manage connectors</Link>
      </Card>
      <Card title="Privacy & Data">
        <PreferenceRow description="When enabled, completed queries and their actual result/source counts are saved to your authenticated account's search history." title="Save search history">
          <label className="flex min-h-10 items-center gap-3 text-sm text-ink"><input aria-label="Save search history" checked={preferences.saveSearchHistory} className="size-4 accent-forest" onChange={(event) => updatePreferences({ ...preferences, saveSearchHistory: event.target.checked })} type="checkbox" /><span>{preferences.saveSearchHistory ? "Enabled" : "Disabled"}</span></label>
        </PreferenceRow>
        <PreferenceRow description="Choose how many items the Knowledge index displays per page. This display preference is saved in this browser." title="Knowledge items per page">
          <select aria-label="Items per page" className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink" onChange={(event) => updatePreferences({ ...preferences, knowledgePageSize: Number(event.target.value) })} value={preferences.knowledgePageSize}><option value={10}>10 items</option><option value={20}>20 items</option><option value={50}>50 items</option></select>
        </PreferenceRow>
        <p className="mt-4 text-sm leading-6 text-ink-muted">Indexed-item deletion and other privacy controls are not currently provided by the API. SMRITI indexes source metadata and content for retrieval; source files remain under their original owners.</p>
        <div className="mt-4 border-t border-line pt-4">
          <h3 className="text-sm font-medium text-ink">Search history</h3>
          <p className="mt-1 text-xs leading-5 text-ink-muted">Delete your persisted query history from your account. This does not remove indexed source items.</p>
          <Button className="mt-3" disabled={clearingHistory} onClick={() => void clearHistory()} variant="secondary">{clearingHistory ? "Clearing…" : "Clear search history"}</Button>
        </div>
      </Card>
      <Card title="Appearance">
        <PreferenceRow description="Choose a light or dark appearance for this account in this browser." title="Theme">
          <select aria-label="Theme" className="min-h-10 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink" onChange={(event) => updatePreferences({ ...preferences, theme: event.target.value as WorkspacePreferences["theme"] })} value={preferences.theme}><option value="light">Light</option><option value="dark">Dark</option></select>
        </PreferenceRow>
      </Card>
    </div>
    {settingsError && <div className="mt-4"><LoadError message={settingsError} /></div>}
    {saved && <p aria-live="polite" className="mt-4 text-sm text-success">Preference saved in this browser.</p>}
  </PageContainer>;
}

export function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const [displayName, setDisplayName] = useState(user?.display_name ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  useEffect(() => {
    setDisplayName(user?.display_name ?? "");
  }, [user?.display_name]);
  if (!user) return null;
  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await updateProfile(displayName);
      setSuccess("Your profile has been updated.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not update your profile.");
    } finally {
      setSaving(false);
    }
  };
  return <PageContainer>
    <PageHeading title="Profile" subtitle="Your authenticated SMRITI account information." />
    <Card className="max-w-2xl" title="Profile information">
      {user.avatar_url && <img alt="" className="mb-5 size-16 rounded-full object-cover" src={user.avatar_url} />}
      <form className="grid gap-5" onSubmit={(event) => void saveProfile(event)}>
        <label className="grid gap-2 text-sm font-medium text-ink" htmlFor="profile-name">Name
          <input autoComplete="name" className="min-h-11 rounded-md border border-line bg-surface px-3 font-normal outline-none focus:border-bronze focus-visible:ring-2 focus-visible:ring-focus-ring/30" id="profile-name" maxLength={255} onChange={(event) => setDisplayName(event.target.value)} value={displayName} />
        </label>
        <label className="grid gap-2 text-sm font-medium text-ink" htmlFor="profile-email">Email
          <input className="min-h-11 rounded-md border border-line bg-surface-muted px-3 font-normal text-ink-muted" id="profile-email" readOnly value={user.email} />
        </label>
        <dl className="grid gap-3 border-t border-line pt-4 sm:grid-cols-2">
          <div><dt className="text-xs text-ink-muted">Email status</dt><dd className="mt-1 text-sm font-medium text-ink">{user.is_verified ? "Verified" : "Not verified"}</dd></div>
          <div><dt className="text-xs text-ink-muted">Member since</dt><dd className="mt-1 text-sm font-medium text-ink">{formatDate(user.created_at)}</dd></div>
        </dl>
        {error && <LoadError message={error} />}
        {success && <p className="text-sm text-success" role="status">{success}</p>}
        <div><Button disabled={saving || displayName.length > 255 || displayName === (user.display_name ?? "")}>{saving ? "Saving…" : "Save profile"}</Button></div>
      </form>
    </Card>
  </PageContainer>;
}
