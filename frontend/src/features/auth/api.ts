export type User = {
  id: number;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
};

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      `Could not connect to the SMRITI API at ${API_BASE_URL}. Check that the backend is running.`,
    );
  }

  if (!response.ok) {
    const body = await response.text();
    let message = response.statusText || "The request failed.";

    if (body) {
      try {
        const parsed: unknown = JSON.parse(body);
        if (
          typeof parsed === "object" &&
          parsed !== null &&
          "detail" in parsed
        ) {
          const { detail } = parsed;
          if (typeof detail === "string") {
            message = detail;
          } else if (Array.isArray(detail)) {
            message = detail
              .map((issue: unknown) => {
                if (
                  typeof issue === "object" &&
                  issue !== null &&
                  "msg" in issue &&
                  typeof issue.msg === "string"
                ) {
                  return issue.msg;
                }
                return "";
              })
              .filter(Boolean)
              .join(" ");
          }
        }
      } catch {
        message = body;
      }
    }

    throw new ApiError(message || "The request failed.", response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function postJson<T>(path: string, body: unknown, accessToken?: string) {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  return apiRequest<T>(path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}
