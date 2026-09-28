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
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
        <p className="font-medium">Could not reach the backend API.</p>
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
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Management Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Estimated values are based on configured assumptions. Observed values come from connected work
          activity. ROI represents modeled economic value and is not causal proof of productivity improvement.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {d.tasks_missing_cost_data} of {d.tasks_with_cost_data + d.tasks_missing_cost_data} tasks with a calculated
          labor value have no available AI cost data, so they are excluded from aggregate AI spend and ROI.
        </div>
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
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="text-sm font-medium text-gray-700">Department Breakdown</h3>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
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
          </table>
        </div>
      </div>
    </div>
  );
}
