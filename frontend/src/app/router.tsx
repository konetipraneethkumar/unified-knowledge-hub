import { createBrowserRouter, Navigate, Outlet, useLocation } from "react-router";
import { AppLayout } from "./layouts/AppLayout";
import { ChatPage } from "../features/chat/components/ChatPage";
import {
  ConnectorsPage,
  DashboardPage,
  HistoryPage,
  SettingsPage,
} from "../features/workspace/WorkspacePages";
import { LandingRoute } from "../pages/LandingRoute";
import { AuthPage } from "../pages/AuthPage";
import { useAuth } from "../features/auth/AuthContext";

function ProtectedRoutes() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <main className="p-8 text-center" aria-live="polite">Restoring your session…</main>;
  }

  if (!user) {
    return <Navigate to="/auth?mode=login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export const router = createBrowserRouter([
  { path: "/", element: <LandingRoute /> },
  { path: "/auth", element: <AuthPage /> },
  {
    element: <ProtectedRoutes />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "search", element: <ChatPage /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "knowledge", element: <Navigate to="/dashboard" replace /> },
          { path: "connectors", element: <ConnectorsPage /> },
          { path: "sync", element: <Navigate to="/connectors" replace /> },
          { path: "history", element: <HistoryPage /> },
          { path: "settings", element: <SettingsPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
