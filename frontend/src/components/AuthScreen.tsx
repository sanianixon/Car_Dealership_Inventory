/**
 * Sign in and registration, as one card with two modes.
 *
 * Field-level messages come from the API's error details, so the rules shown
 * to the user are the ones the server actually enforces rather than a second
 * copy that can drift out of step.
 */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import { useAuth } from "../auth-context";

type Mode = "signIn" | "signUp";

export function AuthScreen() {
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<Mode>("signIn");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [adminCode, setAdminCode] = useState("");
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [busy, setBusy] = useState(false);

  const fieldError = (path: string) =>
    error instanceof ApiError ? error.fieldError(path) : undefined;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "signIn") await signIn(email, password);
      else await signUp(email, password, adminCode.trim() || undefined);
    } catch (caught) {
      setError(caught as Error);
    } finally {
      setBusy(false);
    }
  }

  function switchTo(next: Mode) {
    setMode(next);
    setError(null);
  }

  const inputClass =
    "w-full rounded-lg border border-forecourt-300 bg-white px-3 py-2.5 text-forecourt-900 " +
    "placeholder:text-forecourt-500 focus:border-petrol-600 focus:outline-none";

  return (
    <main className="flex min-h-screen items-center justify-center bg-forecourt-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-petrol-600 text-xl font-bold text-white">
            CD
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-forecourt-900">
            Car Dealership Inventory
          </h1>
          <p className="mt-1 text-sm text-forecourt-500">
            Sign in to browse and buy from the forecourt.
          </p>
        </div>

        <div className="rounded-2xl border border-forecourt-100 bg-white p-6 shadow-sm">
          <div
            className="mb-6 grid grid-cols-2 gap-1 rounded-lg bg-forecourt-100 p-1"
            role="tablist"
          >
            {(["signIn", "signUp"] as Mode[]).map((option) => (
              <button
                key={option}
                type="button"
                role="tab"
                aria-selected={mode === option}
                onClick={() => switchTo(option)}
                className={
                  "rounded-md px-3 py-2 text-sm font-semibold transition " +
                  (mode === option
                    ? "bg-white text-petrol-700 shadow-sm"
                    : "text-forecourt-500 hover:text-forecourt-700")
                }
              >
                {option === "signIn" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className={inputClass}
                placeholder="you@dealership.com"
              />
              {fieldError("email") && (
                <p className="mt-1.5 text-sm text-tag-red">{fieldError("email")}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={mode === "signIn" ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className={inputClass}
                placeholder={mode === "signUp" ? "At least 8 characters" : "••••••••"}
              />
              {fieldError("password") && (
                <p className="mt-1.5 text-sm text-tag-red">{fieldError("password")}</p>
              )}
            </div>

            {mode === "signUp" && (
              <div>
                <label htmlFor="adminCode" className="mb-1.5 block text-sm font-medium">
                  Admin code{" "}
                  <span className="font-normal text-forecourt-500">(optional)</span>
                </label>
                <input
                  id="adminCode"
                  type="text"
                  value={adminCode}
                  onChange={(event) => setAdminCode(event.target.value)}
                  className={inputClass}
                  placeholder="Leave blank for a buyer account"
                />
                <p className="mt-1.5 text-xs text-forecourt-500">
                  Staff only. An invite code grants permission to manage stock.
                </p>
              </div>
            )}

            {error && !fieldError("email") && !fieldError("password") && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2.5 text-sm text-tag-red">
                {error.message}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-petrol-600 px-4 py-2.5 font-semibold text-white transition hover:bg-petrol-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {busy ? "Please wait…" : mode === "signIn" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}
