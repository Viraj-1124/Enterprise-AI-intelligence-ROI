"use client";

import { createContext, FormEvent, ReactNode, useContext, useEffect, useState } from "react";
import { api, AuthUser } from "@/lib/api";

type AuthContextValue = { user: AuthUser | null; setUser: (user: AuthUser | null) => void; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void };
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem("eai_access_token");
    if (!token) { Promise.resolve().then(() => { if (active) setLoading(false); }); return () => { active = false; }; }
    api.me().then(current => { if (active) setUser(current); })
      .catch(() => { localStorage.removeItem("eai_access_token"); if (active) setUser(null); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    localStorage.setItem("eai_access_token", result.access_token);
    try { setUser(await api.me()); }
    catch (error) { localStorage.removeItem("eai_access_token"); throw error; }
  }

  function logout() {
    localStorage.removeItem("eai_access_token");
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, setUser, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}

export function AuthGate({ children }: { children: ReactNode }) {
  const { user, loading, login, setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [setupRequired, setSetupRequired] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;
    api.bootstrapStatus().then(status => { if (active) setSetupRequired(status.setup_required); }).catch(() => {});
    return () => { active = false; };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setSubmitting(true);
    try {
      if (setupRequired) {
        const result = await api.bootstrap({ name, email, password });
        localStorage.setItem("eai_access_token", result.access_token);
        setUser(await api.me());
      } else await login(email, password);
    }
    catch (e) { setError(e instanceof Error ? e.message.replace(/^API error \d+: /, "") : "Sign in failed"); }
    finally { setSubmitting(false); }
  }

  if (loading) return <div className="flex min-h-[65vh] items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" aria-label="Loading account" /></div>;
  if (!user) return <div className="mx-auto flex min-h-[70vh] max-w-md items-center justify-center">
    <div className="w-full rounded-3xl border border-slate-200 bg-white p-7 shadow-xl shadow-slate-900/[0.05] sm:p-9">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-700 text-white"><svg viewBox="0 0 24 24" fill="none" className="h-6 w-6"><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/></svg></div>
      <p className="mt-6 text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Enterprise AI Intelligence</p><h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{setupRequired ? "Set up your workspace" : "Welcome back"}</h1><p className="mt-2 text-sm leading-6 text-slate-500">{setupRequired ? "Create the first administrator account to get started." : "Sign in with your work account to see your workspace."}</p>
      <form onSubmit={submit} className="mt-6 space-y-4">{setupRequired && <label className="block text-sm font-medium text-slate-700">Your name<input required autoComplete="name" value={name} onChange={e => setName(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-3 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100" placeholder="Name" /></label>}<label className="block text-sm font-medium text-slate-700">Work email<input required type="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-3 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100" placeholder="you@company.com" /></label>
        <label className="block text-sm font-medium text-slate-700">Password<input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3.5 py-3 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100" placeholder="Enter your password" /></label>
        {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700">{error}</p>}
        <button disabled={submitting} className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-60">{submitting ? "Signing in…" : "Sign in"}</button>
      </form><p className="mt-5 text-center text-xs leading-5 text-slate-400">{setupRequired ? "You’ll be able to invite employees after signing in." : "Need an account? Ask your workspace manager to create one."}</p>
    </div>
  </div>;
  return <>{children}</>;
}

export function RoleGate({ children, roles }: { children: ReactNode; roles: string[] }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return <div className="mx-auto mt-10 max-w-xl rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900"><p className="font-semibold">This page isn’t available for your role.</p><p className="mt-1">Use the navigation to open the tools assigned to your account.</p></div>;
  return <>{children}</>;
}
