import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ConnectorsPage() {
  const connectors = await api.connectors().catch(() => []);
  const available = connectors.filter(c => c.available).length;

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Integrations</p><h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Connectors</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Connectors bring measured AI usage and work activity into your analytics. Availability reflects the configured integration state.</p></div><span className="inline-flex w-fit items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />{available} of {connectors.length} available</span></div>
    {connectors.length > 0 ? <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">{connectors.map((c) => <section key={c.name} className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4"><div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-sm font-semibold uppercase text-slate-600">{c.name.slice(0, 1)}</span><div><h2 className="font-semibold capitalize text-slate-900">{c.name}</h2><p className="mt-0.5 text-xs text-slate-400">Data connector</p></div></div><span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${c.available ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}><span className={`h-1.5 w-1.5 rounded-full ${c.available ? "bg-emerald-500" : "bg-slate-400"}`} />{c.available ? "Available" : "Unavailable"}</span></div>
      <p className="mt-4 min-h-12 text-sm leading-6 text-slate-500">{c.reason}</p>
    </section>)}</div> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><p className="font-medium text-slate-800">Connector status is unavailable</p><p className="mt-1 text-sm text-slate-500">Check that the backend service is running and try again.</p></div>}
    <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4 text-sm leading-6 text-indigo-900"><span className="font-semibold">Data integrity:</span> when an external source cannot provide reliable usage data, the platform reports it as unavailable instead of estimating silently.</div>
  </div>;
}
