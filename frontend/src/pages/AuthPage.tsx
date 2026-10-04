import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { API_BASE_URL } from "../features/auth/api";
import { useAuth } from "../features/auth/AuthContext";
import "./AuthPage.css";

type ReturnLocation = {
  pathname: string;
  search?: string;
  hash?: string;
};

export function AuthPage() {
  const { user, isLoading, login, register } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const isRegistering = searchParams.get("mode") === "register";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isLoading) {
    return <main className="auth-page" aria-live="polite">Restoring your session…</main>;
  }

  if (user && !isSubmitting) {
    return <Navigate to="/dashboard" replace />;
  }

  const returnLocation = (location.state as { from?: ReturnLocation } | null)?.from;
  const returnTo = returnLocation
    ? `${returnLocation.pathname}${returnLocation.search ?? ""}${returnLocation.hash ?? ""}`
    : "/dashboard";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      if (isRegistering) {
        await register(email, password, displayName);
      } else {
        await login(email, password);
      }
      navigate(returnTo, { replace: true });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Authentication failed. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section aria-labelledby="auth-title" className="auth-card">
        <Link aria-label="SMRITI home" className="auth-brand" to="/">
          <span aria-hidden="true">✦</span> SMRITI
        </Link>
        <p className="auth-eyebrow">YOUR DIGITAL MEMORY</p>
        <h1 id="auth-title">{isRegistering ? "Create your account" : "Welcome back"}</h1>
        <p className="auth-intro">
          {isRegistering
            ? "Start bringing your knowledge together."
            : "Sign in to continue to your knowledge hub."}
        </p>

        <form className="auth-form" onSubmit={(event) => void submit(event)}>
          {isRegistering && (
            <Input
              autoComplete="name"
              label="Name (optional)"
              maxLength={255}
              onChange={(event) => setDisplayName(event.target.value)}
              value={displayName}
            />
          )}
          <Input
            autoComplete="email"
            label="Email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          <Input
            autoComplete={isRegistering ? "new-password" : "current-password"}
            label="Password"
            minLength={12}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {isRegistering && (
            <p className="auth-hint">Use at least 12 characters.</p>
          )}
          {error && <p className="auth-error" role="alert">{error}</p>}
          <Button className="auth-submit" disabled={isSubmitting} type="submit">
            {isSubmitting
              ? "Please wait…"
              : isRegistering
                ? "Create account"
                : "Sign in"}
          </Button>
        </form>

        <div className="auth-divider"><span>or</span></div>
        <Button
          className="auth-google"
          onClick={() => window.location.assign(`${API_BASE_URL}/api/v1/auth/google/login`)}
          variant="secondary"
        >
          Continue with Google
        </Button>
        <p className="auth-switch">
          {isRegistering ? "Already have an account?" : "New to SMRITI?"}{" "}
          <button
            onClick={() => {
              setError("");
              setSearchParams(isRegistering ? { mode: "login" } : { mode: "register" });
            }}
            type="button"
          >
            {isRegistering ? "Sign in" : "Create an account"}
          </button>
        </p>
        <Link className="auth-home" to="/">Back to home</Link>
      </section>
    </main>
  );
}
