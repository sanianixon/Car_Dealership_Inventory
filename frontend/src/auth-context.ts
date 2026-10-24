/**
 * The auth context and its hook, kept apart from the provider component.
 *
 * A module that exports a component should export only components, so that
 * fast refresh can replace it without discarding state. The provider lives in
 * auth.tsx; the context and hook live here.
 */

import { createContext, useContext } from "react";

import type { User } from "./types";

export interface AuthValue {
  user: User | null;
  /** True until the stored token has been checked, so the UI can avoid flicker. */
  initialising: boolean;
  isAdmin: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, adminCode?: string) => Promise<void>;
  signOut: () => void;
}

export const AuthContext = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (value === null) throw new Error("useAuth must be used inside an AuthProvider");
  return value;
}
