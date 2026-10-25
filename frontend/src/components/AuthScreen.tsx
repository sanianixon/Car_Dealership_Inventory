/**
 * Sign in and registration.
 *
 * A split layout rather than a centred card: the left panel carries the name
 * and sets the tone, the right does the work. On a phone the panel collapses
 * to a header so the form stays above the fold.
 *
 * Field-level messages come from the API's error details, so the rules shown
 * to the user are the ones the server actually enforces rather than a second
 * copy that can drift out of step.
 */

import { useState, type FormEvent } from "react";

import { ApiError } from "../api";
import { useAuth } from "../auth-context";

type Mode = "signIn" | "signUp";

const FIELD =
  "w-full border-0 border-b border-ink-200 bg-transparent px-0 py-2.5 text-ink-900 " +
  "placeholder:text-ink-300 focus:border-clay-600 focus:outline-none focus:ring-0";

const LABEL = "mb-1 block text-xs font-semibold uppercase tracking-widest text-ink-500";

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

  return (
    <div className="min-h-screen bg-paper lg:grid lg:grid-cols-[1.1fr_1fr]">
      {/* Left: the name, set large. Decorative on a phone, where it shrinks. */}
      <aside className="flex flex-col justify-between bg-ink-900 px-6 py-10 text-paper sm:px-10 lg:px-14 lg:py-14">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-ink-300">
          Established inventory
        </p>

        <div className="my-10 lg:my-0">
          <h1 className="text-4xl font-extrabold leading-[0.95] tracking-tight sm:text-5xl lg:text-7xl">
            Car
            <br />
            Dealership
            <br />
            <span className="text-clay-600">Inventory</span>
          </h1>
          <p className="mt-6 max-w-sm text-sm leading-relaxed text-ink-300">
            Every vehicle on the forecourt, with live stock. Buyers browse and
            purchase; staff manage what is on the lot.
          </p>
        </div>

        <dl className="hidden gap-8 text-sm lg:flex">
          <div>
            <dt className="text-ink-500">Stock</dt>
            <dd className="font-semibold">Live, per vehicle</dd>
          </div>
          <div>
            <dt className="text-ink-500">Access</dt>
            <dd className="font-semibold">Token authenticated</dd>
          </div>
        </dl>
      </aside>

      {/* Right: the form. */}
      <main className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex gap-6 border-b border-ink-200" role="tablist">
            {(["signIn", "signUp"] as Mode[]).map((option) => (
              <button
                key={option}
                type="button"
                role="tab"
                aria-selected={mode === option}
                onClick={() => switchTo(option)}
                className={
                  "-mb-px border-b-2 pb-3 text-sm font-semibold transition " +
                  (mode === option
                    ? "border-clay-600 text-ink-900"
                    : "border-transparent text-ink-500 hover:text-ink-700")
                }
              >
                {option === "signIn" ? "Sign in" : "Create account"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            <div>
              <label htmlFor="email" className={LABEL}>
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className={FIELD}
                placeholder="you@dealership.com"
              />
              {fieldError("email") && (
                <p className="mt-2 text-sm text-clay-700">{fieldError("email")}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className={LABEL}>
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={mode === "signIn" ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className={FIELD}
                placeholder={mode === "signUp" ? "At least 8 characters" : "••••••••"}
              />
              {fieldError("password") && (
                <p className="mt-2 text-sm text-clay-700">{fieldError("password")}</p>
              )}
            </div>

            {mode === "signUp" && (
              <div>
                <label htmlFor="adminCode" className={LABEL}>
                  Admin code <span className="font-normal normal-case">(optional)</span>
                </label>
                <input
                  id="adminCode"
                  type="text"
                  value={adminCode}
                  onChange={(event) => setAdminCode(event.target.value)}
                  className={FIELD}
                  placeholder="Leave blank for a buyer account"
                />
                <p className="mt-2 text-xs text-ink-500">
                  Staff only. An invite code grants permission to manage stock.
                </p>
              </div>
            )}

            {error && !fieldError("email") && !fieldError("password") && (
              <p
                role="alert"
                className="border-l-2 border-clay-600 bg-clay-50 px-3 py-2.5 text-sm text-clay-700"
              >
                {error.message}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full bg-ink-900 px-4 py-3.5 text-sm font-semibold uppercase tracking-widest text-paper transition hover:bg-ink-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Please wait…" : mode === "signIn" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
