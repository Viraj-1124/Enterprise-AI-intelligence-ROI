"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { RoleGate, useAuth } from "@/components/AuthProvider";
import { api, Department, Employee, EmployeeConnection } from "@/lib/api";

export default function EmployeesPage() {
  const { user } = useAuth();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [connections, setConnections] = useState<EmployeeConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [departmentId, setDepartmentId] = useState(""); const [role, setRole] = useState("employee"); const [hourlyCost, setHourlyCost] = useState("0");
  const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [busy, setBusy] = useState(false);

  async function load() {
    setLoading(true);
    try { const [people, depts, accounts] = await Promise.all([api.employees(), api.departments(), api.connectorAccounts()]); setEmployees(people); setDepartments(depts); setConnections(accounts); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not load employees"); }
    finally { setLoading(false); }
  }
  useEffect(() => { void Promise.resolve().then(load); }, []);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setNotice(""); setBusy(true);
    try {
      await api.createEmployee({ name, email, password, department_id: departmentId || null, role, hourly_cost: Number(hourlyCost) });
      setName(""); setEmail(""); setPassword(""); setDepartmentId(""); setHourlyCost("0"); setRole("employee"); setShowForm(false);
      setNotice("Employee account created. Share the temporary password securely."); await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not create employee"); }
    finally { setBusy(false); }
  }

  async function remove(employee: Employee) {
    if (!window.confirm(`Delete ${employee.name}? Accounts with tracked work history are protected so analytics remain intact.`)) return;
    setError(""); setNotice("");
    try { await api.deleteEmployee(employee.id); setNotice(`${employee.name} was deleted.`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not delete employee"); }
  }

  return <RoleGate roles={["admin", "manager"]}><div className="space-y-6">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Workspace access</p><h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Employees</h1><p className="mt-2 text-sm text-slate-500">Create accounts and see which supported work accounts have been linked.</p></div><button onClick={() => setShowForm(v => !v)} className="w-fit rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700">{showForm ? "Close form" : "+ Add employee"}</button></div>
    {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error.replace(/^API error \d+: /, "")}</p>}{notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</p>}
    {showForm && <form onSubmit={create} className="rounded-2xl border border-indigo-100 bg-white p-5 shadow-sm sm:p-6"><div className="mb-5"><h2 className="font-semibold text-slate-900">New employee account</h2><p className="mt-1 text-xs text-slate-500">The employee can sign in with this email and temporary password.</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <label className="text-sm font-medium text-slate-700">Full name<input required value={name} onChange={e=>setName(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" placeholder="Alex Morgan" /></label>
      <label className="text-sm font-medium text-slate-700">Work email<input required type="email" value={email} onChange={e=>setEmail(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" placeholder="alex@company.com" /></label>
      <label className="text-sm font-medium text-slate-700">Temporary password<input required minLength={8} type="password" value={password} onChange={e=>setPassword(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" /></label>
      <label className="text-sm font-medium text-slate-700">Department<select value={departmentId} onChange={e=>setDepartmentId(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="">No department</option>{departments.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
      <label className="text-sm font-medium text-slate-700">Role<select value={role} onChange={e=>setRole(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"><option value="employee">Employee</option><option value="manager">Manager</option>{user?.role === "admin" && <option value="admin">Administrator</option>}</select></label>
      <label className="text-sm font-medium text-slate-700">Hourly cost <span className="font-normal text-slate-400">(ROI assumption)</span><input type="number" min="0" step="any" value={hourlyCost} onChange={e=>setHourlyCost(e.target.value)} className="mt-1.5 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" /></label>
    </div><button disabled={busy} className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Creating…" : "Create account"}</button></form>}
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-900">Team directory</h2><p className="mt-0.5 text-xs text-slate-500">{employees.length} active accounts</p></div><span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">{connections.length} linked account{connections.length === 1 ? "" : "s"}</span></div>
      {loading ? <div className="p-12 text-center text-sm text-slate-400">Loading team…</div> : <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr><th className="px-5 py-3 text-left">Employee</th><th className="px-5 py-3 text-left">Department</th><th className="px-5 py-3 text-left">Role</th><th className="px-5 py-3 text-left">Connected accounts</th><th className="px-5 py-3 text-right">Actions</th></tr></thead><tbody>{employees.map(e=>{const linked=connections.filter(c=>c.employee_id===e.id);return <tr key={e.id} className="border-t border-slate-100"><td className="px-5 py-4"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-xs font-semibold uppercase text-indigo-700">{e.name.split(/\s+/).map(n=>n[0]).slice(0,2).join("")}</span><span><Link href={`/employees/${e.id}`} className="block font-medium text-slate-900 hover:text-indigo-700">{e.name}</Link><span className="block text-xs text-slate-400">{e.email}</span></span></div></td><td className="px-5 py-4 text-slate-500">{departments.find(d=>d.id===e.department_id)?.name??"—"}</td><td className="px-5 py-4"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs capitalize text-slate-600">{e.role}</span></td><td className="px-5 py-4">{linked.length ? <div className="flex flex-wrap gap-1.5">{linked.map(c=><span key={c.id} title={c.account_name} className="rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium capitalize text-emerald-700">{c.provider}: {c.account_name}</span>)}</div> : <span className="text-xs text-slate-400">None linked</span>}</td><td className="px-5 py-4 text-right">{e.role !== "admin" && <button onClick={()=>void remove(e)} aria-label={`Delete ${e.name}`} className="rounded-lg px-2.5 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50">Delete</button>}</td></tr>;})}{employees.length===0&&<tr><td colSpan={5} className="px-5 py-14 text-center text-sm text-slate-400">No employee accounts yet.</td></tr>}</tbody></table></div>}
    </div>
  </div></RoleGate>;
}
