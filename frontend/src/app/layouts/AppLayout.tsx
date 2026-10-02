import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Outlet, useLocation } from "react-router";
import { Header } from "../../components/ui/Header";
import { Button } from "../../components/ui/Button";
import { Sidebar } from "../../components/navigation/Sidebar";

export function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const location = useLocation();
  const transitionDuration = reduceMotion ? 0 : 0.18;

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