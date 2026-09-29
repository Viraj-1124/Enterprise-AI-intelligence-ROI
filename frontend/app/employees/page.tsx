import { api, formatValue } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EmployeesPage() {
  const [employees, departments] = await Promise.all([
    api.employees().catch(() => []),
    api.departments().catch(() => []),
  ]);
  const deptName = (id: string | null) => departments.find((d) => d.id === id)?.name ?? "—";

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
      <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Organization</p><h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Employees</h1><p className="mt-2 text-sm text-slate-500">Hourly cost is an ROI configuration assumption, not a productivity score.</p></div>
      <span className="inline-flex w-fit rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm">{employees.length} people</span>
    </div>
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-900/[0.025]">
      <div className="overflow-x-auto"><table className="w-full text-sm">
        <thead className="text-left text-slate-500"><tr><th className="px-5 py-3.5">Name</th><th className="px-5 py-3.5">Email</th><th className="px-5 py-3.5">Department</th><th className="px-5 py-3.5">Role</th><th className="px-5 py-3.5">Hourly cost <span className="font-normal normal-case tracking-normal">(assumption)</span></th></tr></thead>
        <tbody>{employees.map((e) => <tr key={e.id} className="border-t border-slate-100">
          <td className="px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-xs font-semibold uppercase text-indigo-700">{e.name.split(/\s+/).map(n => n[0]).slice(0, 2).join("")}</span><span className="font-medium text-slate-900">{e.name}</span></div></td>
          <td className="px-5 py-4 text-slate-500">{e.email}</td><td className="px-5 py-4 text-slate-500">{deptName(e.department_id)}</td>
          <td className="px-5 py-4"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium capitalize text-slate-600">{e.role}</span></td>
          <td className="px-5 py-4 font-medium text-slate-700">{formatValue(e.hourly_cost, "$")}</td>
        </tr>)}
        {employees.length === 0 && <tr><td colSpan={5} className="px-5 py-14 text-center"><span className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">♙</span><span className="mt-3 block font-medium text-slate-700">No employees yet</span><span className="mt-1 block text-sm text-slate-400">Add employees to organize task and ROI reporting.</span></td></tr>}
        </tbody>
      </table></div>
    </div>
  </div>;
}
