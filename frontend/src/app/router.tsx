import { createBrowserRouter, Navigate } from "react-router";
import { AppLayout } from "./layouts/AppLayout";
import { ChatPage } from "../features/chat/components/ChatPage";
import {
  ConnectorsPage,
  DashboardPage,
  HistoryPage,
  SettingsPage,
} from "../features/workspace/WorkspacePages";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/search" replace /> },
      { path: "search", element: <ChatPage /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "knowledge", element: <Navigate to="/dashboard" replace /> },
      { path: "connectors", element: <ConnectorsPage /> },
      { path: "sync", element: <Navigate to="/connectors" replace /> },
      { path: "history", element: <HistoryPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <Navigate to="/search" replace /> },
    ],
  },
]);