import { api, formatValue } from "@/lib/api";
import KpiCard from "@/components/KpiCard";
import { BarChartCard, PieChartCard } from "@/components/DashboardCharts";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let dashboard;
  let error: string | null = null;
  try {
    dashboard = await api.managementDashboard();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unknown error";
  }

  if (error || !dashboard) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-white p-6 text-rose-800 shadow-sm">
        <p className="font-semibold">Could not reach the backend API.</p>
        <p className="mt-1 text-sm">
          Make sure the FastAPI backend is running at{" "}
          <code className="rounded bg-red-100 px-1">NEXT_PUBLIC_API_BASE_URL</code> (default{" "}
          <code className="rounded bg-red-100 px-1">http://localhost:8000</code>). Error: {error}
        </p>
      </div>
    );
  }

  const d = dashboard;

  return (
    <div className="space-y-7">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Overview</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Management Dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">
          Estimated values are based on configured assumptions. Observed values come from connected work
          activity. ROI represents modeled economic value and is not causal proof of productivity improvement.
        </p></div>
        <div className="inline-flex items-center gap-2 self-start rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 sm:self-auto"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Analytics ready</div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard label="AI Spend" value={formatValue(d.ai_spend.value, "$")} source={d.ai_spend.source} note={d.ai_spend.note} />
        <KpiCard label="AI-Assisted Tasks" value={`${d.ai_assisted_tasks} / ${d.total_tasks}`} source="observed" />
        <KpiCard label="Time Saved" value={`${formatValue(d.time_saved_minutes.value)} min`} source={d.time_saved_minutes.source} />
        <KpiCard label="Estimated Business Value" value={formatValue(d.estimated_business_value.value, "$")} source={d.estimated_business_value.source} />
        <KpiCard label="Net Estimated Value" value={formatValue(d.net_estimated_value.value, "$")} source={d.net_estimated_value.source} />
        <KpiCard label="Estimated ROI" value={typeof d.aggregate_roi_percentage.value === "number" ? `${formatValue(d.aggregate_roi_percentage.value)}%` : "N/A"} source={d.aggregate_roi_percentage.source} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard label="AI Adoption" value={`${d.ai_adoption_pct}%`} source="observed" />
        <KpiCard label="Cost per AI-assisted Task" value={formatValue(d.cost_per_ai_assisted_task, "$")} source={typeof d.cost_per_ai_assisted_task === "number" ? "connector" : "unavailable"} />
        <KpiCard label="ROI Multiple" value={typeof d.roi_multiple.value === "number" ? `${formatValue(d.roi_multiple.value)}x` : "N/A"} source={typeof d.roi_multiple.value === "number" ? "estimated" : "unavailable"} />
      </div>

      {(d.tasks_missing_cost_data > 0) && (
        <div className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-4 text-sm leading-6 text-amber-900">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-100 font-semibold">!</span><span>
          {d.tasks_missing_cost_data} of {d.tasks_with_cost_data + d.tasks_missing_cost_data} tasks with a calculated
          labor value have no available AI cost data, so they are excluded from aggregate AI spend and ROI.
          </span></div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <BarChartCard
          title="Time Saved by Department (minutes)"
          data={d.department_stats.map((s) => ({ name: s.department, value: Math.round(s.time_saved_minutes) }))}
        />
        <BarChartCard
          title="AI Adoption by Department (%)"
          data={d.department_stats.map((s) => ({ name: s.department, value: s.ai_adoption_pct }))}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PieChartCard
          title="AI Usage by Provider (events)"
          data={Object.entries(d.provider_stats).map(([name, s]) => ({ name, value: s.events }))}
        />
        <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] sm:p-6">
          <h3 className="text-sm font-semibold text-slate-800">Department Breakdown</h3>
          <div className="mt-4 overflow-x-auto"><table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="pb-2">Department</th>
                <th className="pb-2">Employees</th>
                <th className="pb-2">Tasks</th>
                <th className="pb-2">AI Adoption</th>
                <th className="pb-2">AI Spend</th>
              </tr>
            </thead>
            <tbody>
              {d.department_stats.map((s) => (
                <tr key={s.department_id} className="border-t border-gray-100">
                  <td className="py-2 font-medium text-gray-900">{s.department}</td>
                  <td className="py-2">{s.employees}</td>
                  <td className="py-2">{s.tasks}</td>
                  <td className="py-2">{s.ai_adoption_pct}%</td>
                  <td className="py-2">{formatValue(s.ai_spend, "$")}</td>
                </tr>
              ))}
              {d.department_stats.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-gray-400">
                    No departments yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table></div>
        </div>
      </div>
    </div>
  );
}
