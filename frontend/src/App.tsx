/**
 * Top-level gate: show the auth screen or the dashboard.
 *
 * There is no router. The app has two states, decided by whether anyone is
 * signed in, so a routing library would add a dependency without adding
 * behaviour.
 */

import { AuthScreen } from "./components/AuthScreen";
import { Dashboard } from "./components/Dashboard";
import { useAuth } from "./auth-context";

export default function App() {
  const { user, initialising } = useAuth();

  if (initialising) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-forecourt-50">
        <p className="text-sm text-forecourt-500">Loading…</p>
      </div>
    );
  }

  return user === null ? <AuthScreen /> : <Dashboard />;
}
