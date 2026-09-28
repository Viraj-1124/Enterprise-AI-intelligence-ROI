import { api, formatValue } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DepartmentsPage() {
  const departments = await api.departments().catch(() => []);
  const details = await Promise.all(
    departments.map((d) => api.departmentDashboard(d.id).catch(() => null))
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Departments</h1>
        <p className="mt-1 text-sm text-gray-500">
          Department → Employees → Tasks → Task ROI. Use the Employees and Tasks pages to drill further.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {departments.map((d, i) => {
          const stats = details[i];
          return (
            <div key={d.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="font-medium text-gray-900">{d.name}</h3>
              {stats ? (
                <div className="mt-3 space-y-1 text-sm text-gray-600">
                  <p>Employees: {stats.employees}</p>
                  <p>Tasks: {stats.tasks}</p>
                  <p>AI adoption: {stats.ai_adoption_pct}%</p>
                  <p>Time saved: {formatValue(stats.time_saved_minutes)} min</p>
                  <p>AI spend: {formatValue(stats.ai_spend, "$")}</p>
                  <p>ROI: {typeof stats.roi_percentage === "number" ? `${formatValue(stats.roi_percentage)}%` : "N/A"}</p>
                </div>
              ) : (
                <p className="mt-3 text-sm text-gray-400">No data.</p>
              )}
            </div>
          );
        })}
        {departments.length === 0 && (
          <p className="text-sm text-gray-400">No departments yet. Create one via POST /api/departments (admin only).</p>
        )}
      </div>
    </div>
  );
}
