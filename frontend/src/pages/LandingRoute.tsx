import { Navigate } from "react-router";
import { useAuth } from "../features/auth/AuthContext";
import { LandingPage } from "./LandingPage";

export function LandingRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <main className="landing-loading" aria-live="polite">Loading SMRITI…</main>;
  }

  return user ? <Navigate to="/dashboard" replace /> : <LandingPage />;
}
