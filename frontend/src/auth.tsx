/**
 * Who is signed in, and how that changes.
 *
 * The token is kept in localStorage so a reload does not sign the user out,
 * and is re-validated against /auth/me on start-up: a token can be correctly
 * signed yet belong to an account that no longer exists, and the backend
 * rejects exactly that case.
 */

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, readToken, writeToken } from "./api";
import { AuthContext, type AuthValue } from "./auth-context";
import type { User } from "./types";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [initialising, setInitialising] = useState(true);

  useEffect(() => {
    if (readToken() === null) {
      setInitialising(false);
      return;
    }

    let cancelled = false;
    api
      .me()
      .then(({ user: current }) => {
        if (!cancelled) setUser(current);
      })
      .catch(() => {
        // Expired, tampered with, or the account is gone. Either way, the
        // stored token is useless, so discard it instead of keeping a session
        // that every request would reject.
        writeToken(null);
      })
      .finally(() => {
        if (!cancelled) setInitialising(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const { token, user: signedIn } = await api.login(email, password);
    writeToken(token);
    setUser(signedIn);
  }, []);

  const signUp = useCallback(
    async (email: string, password: string, adminCode?: string) => {
      await api.register(email, password, adminCode);
      // Registration does not return a token, so sign in straight away and
      // the new account lands on the dashboard rather than a second form.
      const { token, user: signedIn } = await api.login(email, password);
      writeToken(token);
      setUser(signedIn);
    },
    [],
  );

  const signOut = useCallback(() => {
    writeToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthValue>(
    () => ({
      user,
      initialising,
      isAdmin: user?.role === "admin",
      signIn,
      signUp,
      signOut,
    }),
    [user, initialising, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
