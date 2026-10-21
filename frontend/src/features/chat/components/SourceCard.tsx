import { Badge } from "../../../components/ui/Badge";
import { Typography } from "../../../components/ui/Typography";
import type { ChatSource } from "../types";
import { useAuth } from "../../auth/AuthContext";
import { readPreferences } from "../../workspace/api";

function metadataString(
  metadata: Record<string, unknown> | null,
  key: string,
) {
  const value = metadata?.[key];
  return typeof value === "string" ? value : null;
}

function safeHttpUrl(value: string | null) {
  if (!value) {
    return null;
  }
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? parsed.href
      : null;
  } catch {
    return null;
  }
}

export function SourceCard({ source }: { source: ChatSource }) {
  const { user } = useAuth();
  const showEvidence = user ? readPreferences(user.id).showEvidence : true;
  const { trusted_source_reference: reference } = source;
  const metadata = reference.metadata;
  const sourceType = source.source_type.toLowerCase();
  const trustedLocation =
    sourceType === "local"
      ? reference.file_path ?? reference.location
      : reference.parent_location ?? reference.location;
  const openUrl = safeHttpUrl(reference.web_url ?? reference.location);
  const attachments = Array.isArray(metadata?.attachments)
    ? metadata.attachments.filter(
        (attachment): attachment is Record<string, unknown> =>
          typeof attachment === "object" &&
          attachment !== null &&
          !Array.isArray(attachment),
      )
    : [];
  const formattedDate = source.date
    ? Number.isNaN(new Date(source.date).getTime())
      ? source.date
      : new Date(source.date).toLocaleString()
    : null;

  return (
    <article className="rounded-xl border border-line bg-surface p-4 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <Typography as="h3" variant="sectionHeading" className="text-base">
          {source.title ?? "Untitled source"}
        </Typography>
        <Badge className="shrink-0" variant="default">
          {source.source_type.replaceAll("_", " ")}
        </Badge>
        {typeof source.relevance_score === "number" && <Badge className="shrink-0" variant="default">Match {source.relevance_score.toFixed(2)}</Badge>}
      </div>

      {showEvidence && <div className="mt-3 rounded-md bg-surface-muted p-3">
        <Typography as="h4" variant="caption" className="font-medium text-ink">
          {source.evidence_label || "Evidence"}
        </Typography>
        <Typography className="mt-1" variant="secondary">
          {source.evidence || "Evidence text unavailable."}
        </Typography>
      </div>}

      <div className="mt-4 space-y-2 text-sm text-ink-muted">
        {formattedDate && (
          <p>
            <span className="font-medium text-ink">Date:</span>{" "}
            {formattedDate}
          </p>
        )}

        {sourceType === "gmail" && (
          <>
            {metadataString(metadata, "sender") && (
              <p>
                <span className="font-medium text-ink">From:</span>{" "}
                {metadataString(metadata, "sender")}
              </p>
            )}
            {metadataString(metadata, "subject") && (
              <p>
                <span className="font-medium text-ink">Subject:</span>{" "}
                {metadataString(metadata, "subject")}
              </p>
            )}
            {metadataString(metadata, "thread_id") && (
              <p className="break-all">
                <span className="font-medium text-ink">Thread:</span>{" "}
                {metadataString(metadata, "thread_id")}
              </p>
            )}
            {metadataString(metadata, "message_id") && (
              <p className="break-all">
                <span className="font-medium text-ink">Message:</span>{" "}
                {metadataString(metadata, "message_id")}
              </p>
            )}
          </>
        )}

        {sourceType === "google_classroom" && (
          <>
            {metadataString(metadata, "course_name") && (
              <p>
                <span className="font-medium text-ink">Course:</span>{" "}
                {metadataString(metadata, "course_name")}
              </p>
            )}
            {metadataString(metadata, "resource_type") && (
              <p>
                <span className="font-medium text-ink">Classwork:</span>{" "}
                {metadataString(metadata, "resource_type")}
              </p>
            )}
            {metadataString(metadata, "resource_id") && (
              <p className="break-all">
                <span className="font-medium text-ink">Resource:</span>{" "}
                {metadataString(metadata, "resource_id")}
              </p>
            )}
            {attachments.map((attachment, index) => {
              const title =
                typeof attachment.title === "string"
                  ? attachment.title
                  : "Attachment";
              const url =
                typeof attachment.url === "string"
                  ? safeHttpUrl(attachment.url)
                  : null;
              return (
                <p key={`${title}-${index}`}>
                  <span className="font-medium text-ink">Attachment:</span>{" "}
                  {title}
                  {url && (
                    <>
                      {" — "}
                      <a
                        className="text-forest underline"
                        href={url}
                        rel="noreferrer"
                        target="_blank"
                      >
                        Open
                      </a>
                    </>
                  )}
                </p>
              );
            })}
          </>
        )}

        <p className="break-all">
          <span className="font-medium text-ink">
            {sourceType === "local"
              ? "Filesystem location:"
              : sourceType === "google_drive"
                ? "Drive location:"
                : sourceType === "gmail"
                  ? "Email location:"
                  : sourceType === "google_classroom"
                    ? "Classroom location:"
                    : "Location:"}
          </span>{" "}
          {trustedLocation || "Location unavailable"}
        </p>

        {sourceType === "google_drive" &&
          Array.isArray(metadata?.parent_ids) &&
          metadata.parent_ids.length > 0 && (
            <p className="break-all">
              <span className="font-medium text-ink">Drive folder IDs:</span>{" "}
              {metadata.parent_ids.filter(
                (parentId): parentId is string => typeof parentId === "string",
              ).join(" / ") || "Location unavailable"}
            </p>
          )}

        {openUrl && (
          <a
            className="inline-flex text-forest underline"
            href={openUrl}
            rel="noreferrer"
            target="_blank"
          >
            {sourceType === "gmail"
              ? "Open email"
              : sourceType === "google_drive"
                ? "Open in Google Drive"
                : sourceType === "google_classroom"
                  ? "Open in Google Classroom"
                  : "Open source"}
          </a>
        )}
      </div>
    </article>
  );
}
