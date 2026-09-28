import { api, formatValue } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EmployeesPage() {
  const [employees, departments] = await Promise.all([
    api.employees().catch(() => []),
    api.departments().catch(() => []),
  ]);
  const deptName = (id: string | null) => departments.find((d) => d.id === id)?.name ?? "—";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Employees</h1>
        <p className="mt-1 text-sm text-gray-500">
          Hourly cost is a configuration assumption used only for ROI estimation, not a productivity score.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Department</th>
              <th className="px-4 py-2">Role</th>
              <th className="px-4 py-2">Hourly cost (assumption)</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((e) => (
              <tr key={e.id} className="border-t border-gray-100">
                <td className="px-4 py-2 font-medium text-gray-900">{e.name}</td>
                <td className="px-4 py-2 text-gray-600">{e.email}</td>
                <td className="px-4 py-2 text-gray-600">{deptName(e.department_id)}</td>
                <td className="px-4 py-2 text-gray-600">{e.role}</td>
                <td className="px-4 py-2 text-gray-600">{formatValue(e.hourly_cost, "$")}</td>
              </tr>
            ))}
            {employees.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No employees yet. Create one via <code>POST /api/employees</code>.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
