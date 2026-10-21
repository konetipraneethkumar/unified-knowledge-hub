import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Outlet, useLocation, useNavigate } from "react-router";
import { Link } from "react-router";
import { Header } from "../../components/ui/Header";
import { Button } from "../../components/ui/Button";
import { Sidebar } from "../../components/navigation/Sidebar";
import { useAuth } from "../../features/auth/AuthContext";
import { readPreferences } from "../../features/workspace/api";

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [logoutError, setLogoutError] = useState("");
  const transitionDuration = reduceMotion ? 0 : 0.18;

  useEffect(() => {
    if (!user) return;
    const applyTheme = () => {
      document.documentElement.dataset.theme = readPreferences(user.id).theme;
    };
    const onPreferenceChange = (event: Event) => {
      const detail = (event as CustomEvent<{ userId?: number }>).detail;
      if (detail?.userId === user.id) applyTheme();
    };
    applyTheme();
    window.addEventListener("smriti-preferences-changed", onPreferenceChange);
    return () => window.removeEventListener("smriti-preferences-changed", onPreferenceChange);
  }, [user]);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileMenuOpen) return;

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileMenuOpen(false);
    };

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Header
        className="relative z-50"
        actions={
          <>
            {logoutError && <span className="text-sm text-error" role="alert">{logoutError}</span>}
            <details className="relative">
              <summary className="flex min-h-10 cursor-pointer list-none items-center gap-2 rounded-md border border-line bg-surface px-2.5 text-left text-sm text-ink hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-focus-ring sm:gap-3 sm:px-3">
                {user?.avatar_url
                  ? <img alt="" className="size-7 rounded-full object-cover" src={user.avatar_url} />
                  : <span aria-hidden="true" className="flex size-7 items-center justify-center rounded-full bg-forest-soft text-xs font-semibold text-forest">{(user?.display_name || user?.email || "U").slice(0, 1).toUpperCase()}</span>}
                <span className="hidden max-w-36 truncate sm:inline">{user?.display_name || user?.email}</span>
                <span aria-hidden="true" className="text-xs">⌄</span>
              </summary>
              <div className="absolute right-0 top-full z-50 mt-2 w-64 rounded-lg border border-line bg-surface p-2 shadow-card">
                <div className="border-b border-line px-3 py-2">
                  <p className="truncate text-sm font-medium text-ink">{user?.display_name || user?.email}</p>
                  {user?.display_name && <p className="truncate text-xs text-ink-muted">{user.email}</p>}
                </div>
                <Link className="block rounded-md px-3 py-2 text-sm text-ink hover:bg-surface-muted" onClick={(event) => { event.currentTarget.closest("details")?.removeAttribute("open"); }} to="/profile">Profile</Link>
                <Link className="block rounded-md px-3 py-2 text-sm text-ink hover:bg-surface-muted" onClick={(event) => { event.currentTarget.closest("details")?.removeAttribute("open"); }} to="/settings">Settings</Link>
                <Button
                  className="mt-1 w-full justify-start"
                  onClick={() => {
                    setLogoutError("");
                    void logout()
                      .then(() => navigate("/", { replace: true }))
                      .catch((error: unknown) => {
                        setLogoutError(error instanceof Error ? error.message : "Could not sign out.");
                      });
                  }}
                  variant="ghost"
                >
                  Sign out
                </Button>
              </div>
            </details>
            <Button
              aria-controls="mobile-navigation"
              aria-expanded={mobileMenuOpen}
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
              className="gap-2 px-3 md:hidden"
              onClick={() => setMobileMenuOpen((open) => !open)}
              variant="ghost"
            >
              <span aria-hidden="true" className="flex w-4 flex-col gap-1">
                <span className="h-px w-full bg-current" />
                <span className="h-px w-full bg-current" />
                <span className="h-px w-full bg-current" />
              </span>
              <span className="sr-only">Menu</span>
            </Button>
          </>
        }
      />

      <div className="flex min-h-[calc(100vh-4rem)]">
        <div className="hidden shrink-0 md:block">
          <Sidebar />
        </div>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            animate={{ opacity: 1 }}
            className="fixed inset-x-0 bottom-0 top-16 z-40 md:hidden"
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            transition={{ duration: transitionDuration }}
          >
            <button
              aria-label="Close navigation menu"
              className="absolute inset-0 size-full bg-black/25"
              onClick={() => setMobileMenuOpen(false)}
              type="button"
            />
            <motion.div
              animate={{ x: 0 }}
              className="absolute inset-y-0 left-0"
              exit={{ x: "-100%" }}
              initial={{ x: "-100%" }}
              id="mobile-navigation"
              transition={{ duration: transitionDuration, ease: "easeOut" }}
            >
              <Sidebar onNavigate={() => setMobileMenuOpen(false)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}