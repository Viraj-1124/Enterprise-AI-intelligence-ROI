import { api, formatValue } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DepartmentsPage() {
  const departments = await api.departments().catch(() => []);
  const details = await Promise.all(departments.map((d) => api.departmentDashboard(d.id).catch(() => null)));

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Organization</p><h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Departments</h1><p className="mt-2 text-sm text-slate-500">A clear view of AI adoption, time saved, and value across teams.</p></div><span className="inline-flex w-fit rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm">{departments.length} teams</span></div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {departments.map((d, i) => {
        const stats = details[i];
        return <section key={d.id} className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-900/[0.025] transition hover:-translate-y-0.5 hover:shadow-md">
          <div className="flex items-center gap-3 border-b border-slate-100 px-5 py-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-sm font-semibold text-indigo-700">{d.name.slice(0, 1).toUpperCase()}</span><div><h2 className="font-semibold text-slate-900">{d.name}</h2><p className="text-xs text-slate-400">Department overview</p></div></div>
          {stats ? <div className="p-5"><div className="grid grid-cols-2 gap-3"><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">Employees</p><p className="mt-1 text-lg font-semibold text-slate-900">{stats.employees}</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">Tasks</p><p className="mt-1 text-lg font-semibold text-slate-900">{stats.tasks}</p></div></div>
            <div className="mt-5"><div className="flex justify-between text-xs"><span className="font-medium text-slate-600">AI adoption</span><span className="font-semibold text-indigo-700">{stats.ai_adoption_pct}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500" style={{ width: `${Math.max(0, Math.min(100, stats.ai_adoption_pct))}%` }} /></div></div>
            <dl className="mt-5 space-y-3 border-t border-slate-100 pt-4 text-sm"><div className="flex justify-between"><dt className="text-slate-500">Time saved</dt><dd className="font-medium text-slate-800">{formatValue(stats.time_saved_minutes)} min</dd></div><div className="flex justify-between"><dt className="text-slate-500">AI spend</dt><dd className="font-medium text-slate-800">{formatValue(stats.ai_spend, "$")}</dd></div><div className="flex justify-between"><dt className="text-slate-500">Estimated ROI</dt><dd className="font-semibold text-slate-800">{typeof stats.roi_percentage === "number" ? `${formatValue(stats.roi_percentage)}%` : "N/A"}</dd></div></dl>
          </div> : <p className="p-5 text-sm text-slate-400">Department metrics are not available right now.</p>}
        </section>;
      })}
      {departments.length === 0 && <div className="col-span-full rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><span className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">⌂</span><p className="mt-3 font-medium text-slate-800">No departments yet</p><p className="mt-1 text-sm text-slate-500">Create departments to compare adoption and ROI by team.</p></div>}
    </div>
  </div>;
}
