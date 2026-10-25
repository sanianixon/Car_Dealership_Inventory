/**
 * Top-level gate and routing.
 *
 * Not signed in, there is one screen. Signed in, there are two: the forecourt
 * and a model's own page. A router earns its place now that a model page has
 * its own URL — a buyer can be sent a link to a specific model, and the back
 * button behaves.
 */

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthScreen } from "./components/AuthScreen";
import { Dashboard } from "./components/Dashboard";
import { ModelPage } from "./pages/ModelPage";
import { useAuth } from "./auth-context";

export default function App() {
  const { user, initialising } = useAuth();

  if (initialising) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <p className="text-sm text-ink-500">Loading…</p>
      </div>
    );
  }

  if (user === null) return <AuthScreen />;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/vehicles/:id" element={<ModelPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
