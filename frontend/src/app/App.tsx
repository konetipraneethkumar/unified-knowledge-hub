import { RouterProvider } from "react-router";
import { router } from "./router";
import { AuthProvider } from "../features/auth/AuthContext";

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}