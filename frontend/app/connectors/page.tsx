"use client";

import { useEffect, useState } from "react";
import { api, ConnectorStatus, EmployeeConnection } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export default function ConnectorsPage() {
  const { user } = useAuth();
  const manager = user?.role === "admin" || user?.role === "manager";
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
  const [accounts, setAccounts] = useState<EmployeeConnection[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const reload = async () => {
    const [c, a] = await Promise.all([api.connectors(), api.connectorAccounts()]);
    setConnectors(c); setAccounts(a);
  };
  useEffect(() => {
    let active = true;
    Promise.all([api.connectors(), api.connectorAccounts()]).then(([c, a]) => { if (active) { setConnectors(c); setAccounts(a); } }).catch(e => { if (active) setError(e.message); });
    Promise.resolve().then(() => {
      const params = new URLSearchParams(window.location.search);
      const connected = params.get("connected");
      const connectionError = params.get("connection_error");
      if (connected) setMessage(`${connected} account connected successfully.`);
      if (connectionError) setError(`Connection failed: ${connectionError.replaceAll("_", " ")}.`);
    });
    return () => { active = false; };
  }, [manager]);
  const accountForProvider = (provider: string) => accounts.find(a => a.provider === provider && (manager || a.employee_id === user?.id));
  async function connect(provider: string) {
    setBusy(provider); setError("");
    try { await api.startOAuth(provider); } catch (e) { setError(e instanceof Error ? e.message : "Could not start OAuth"); setBusy(""); }
  }
  async function disconnect(provider: string) {
    setBusy(provider); setError("");
    try { await api.disconnectAccount(provider); await reload(); setMessage(`${provider} account disconnected.`); } catch (e) { setError(e instanceof Error ? e.message : "Could not disconnect account"); } finally { setBusy(""); }
  }
  return <div className="space-y-6">
    <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Integrations</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Connectors</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Employees can link supported accounts. Managers can review which accounts are linked across the workspace.</p></div><span className="w-fit rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600">{connectors.filter(c => c.available).length} of {connectors.length} available</span></header>
    {message && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</p>}{error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{connectors.map(c => {
      const linked = accountForProvider(c.name);
      return <section key={c.name} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><h2 className="font-semibold capitalize text-slate-900">{c.name}</h2><p className="mt-1 text-xs text-slate-500">{c.available ? "Workspace integration configured" : "Not configured"}</p></div><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${c.available ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{c.available ? "Available" : "Unavailable"}</span></div><p className="mt-4 min-h-12 text-sm leading-6 text-slate-500">{c.reason}</p>{c.name === "github" && c.oauth_supported ? linked ? <div className="mt-4 flex items-center justify-between gap-2 rounded-xl bg-emerald-50 px-3 py-2.5"><span className="truncate text-sm font-medium text-emerald-800">Connected as @{linked.account_name}</span><button disabled={!!busy} onClick={() => disconnect(c.name)} className="text-xs font-semibold text-emerald-800 underline disabled:opacity-50">Disconnect</button></div> : <button disabled={!!busy} onClick={() => connect(c.name)} className="mt-4 w-full rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:opacity-50">{busy === c.name ? "Opening GitHub…" : "Connect GitHub account"}</button> : <p className="mt-4 rounded-xl bg-slate-50 px-3 py-2.5 text-xs leading-5 text-slate-500">Personal OAuth is not available for this provider. Usage is included only when reliably reported by the configured workspace integration.</p>}</section>;
    })}</div>
    {manager && <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-900">Employee account links</h2><p className="mt-1 text-xs text-slate-500">Linked identities are visible to workspace managers.</p></div>{accounts.length ? <div className="divide-y divide-slate-100">{accounts.map(a => <div key={a.id} className="flex items-center justify-between gap-3 px-5 py-3"><div><p className="text-sm font-medium text-slate-900">{a.employee_name || "Employee"}</p><p className="text-xs text-slate-500">{a.provider} · @{a.account_name}</p></div><time className="text-xs text-slate-400">{new Date(a.connected_at).toLocaleDateString()}</time></div>)}</div> : <p className="px-5 py-8 text-sm text-slate-500">No employee accounts linked yet.</p>}</section>}
    <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4 text-sm leading-6 text-indigo-900"><span className="font-semibold">Usage visibility:</span> managers can review employee tasks, AI usage events, and ROI captured in this platform. Linking a GitHub identity currently records the account only; it does not import repository activity.</div>
  </div>;
}
