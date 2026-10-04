import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { ApiError, apiRequest, postJson, type AuthSession, type User } from "./api";

const ACCESS_TOKEN_KEY = "smriti.accessToken";
const REFRESH_TOKEN_KEY = "smriti.refreshToken";
let sessionRestore: Promise<User | null> | null = null;

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function saveSession(session: AuthSession) {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, session.access_token);
  sessionStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token);
}

function clearSession() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isCurrent = true;

    function restoreSession() {
      if (sessionRestore) {
        return sessionRestore;
      }

      sessionRestore = (async () => {
        try {
          const currentUrl = new URL(window.location.href);
          const oauthAccessToken = currentUrl.searchParams.get("access_token");
          const oauthRefreshToken = currentUrl.searchParams.get("refresh_token");

          if (oauthAccessToken || oauthRefreshToken) {
            currentUrl.searchParams.delete("access_token");
            currentUrl.searchParams.delete("refresh_token");
            window.history.replaceState(
              window.history.state,
              "",
              `${currentUrl.pathname}${currentUrl.search}${currentUrl.hash}`,
            );

            if (oauthAccessToken && oauthRefreshToken) {
              sessionStorage.setItem(ACCESS_TOKEN_KEY, oauthAccessToken);
              sessionStorage.setItem(REFRESH_TOKEN_KEY, oauthRefreshToken);
            }
          }

          const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
          const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
          if (!accessToken || !refreshToken) {
            clearSession();
            return null;
          }

          try {
            return await apiRequest<User>("/api/v1/auth/me", {
              headers: { Authorization: `Bearer ${accessToken}` },
            });
          } catch (error) {
            if (!(error instanceof ApiError) || error.status !== 401) {
              throw error;
            }

            const refreshed = await postJson<AuthSession>(
              "/api/v1/auth/refresh",
              { refresh_token: refreshToken },
            );
            saveSession(refreshed);
            return refreshed.user;
          }
        } catch (error) {
          if (error instanceof ApiError && error.status === 401) {
            clearSession();
          }
          return null;
        }
      })();

      return sessionRestore;
    }

    void restoreSession().then((restoredUser) => {
      if (isCurrent) {
        setUser(restoredUser);
        setIsLoading(false);
      }
    });

    return () => {
      isCurrent = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session = await postJson<AuthSession>("/api/v1/auth/login", {
      email,
      password,
    });
    saveSession(session);
    setUser(session.user);
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName: string) => {
      const session = await postJson<AuthSession>("/api/v1/auth/register", {
        email,
        password,
        display_name: displayName.trim() || null,
      });
      saveSession(session);
      setUser(session.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = sessionStorage.getItem(REFRESH_TOKEN_KEY);
    try {
      if (accessToken) {
        try {
          await apiRequest<void>("/api/v1/auth/logout", {
            method: "POST",
            headers: { Authorization: `Bearer ${accessToken}` },
          });
        } catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401 || !refreshToken) {
            throw error;
          }

          const refreshed = await postJson<AuthSession>(
            "/api/v1/auth/refresh",
            { refresh_token: refreshToken },
          );
          await apiRequest<void>("/api/v1/auth/logout", {
            method: "POST",
            headers: { Authorization: `Bearer ${refreshed.access_token}` },
          });
        }
      }
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, login, register, logout }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
