"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { RoleGate } from "@/components/AuthProvider";
import { api, Employee, EmployeeDashboard, Task, formatValue } from "@/lib/api";

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [summary, setSummary] = useState<EmployeeDashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; Promise.all([api.employees(), api.employeeDashboard(id), api.tasks({ employee_id: id })]).then(([employees, dashboard, rows]) => { if (active) { setEmployee(employees.find(e => e.id === id) || null); setSummary(dashboard); setTasks(rows); } }).catch(e => { if (active) setError(e instanceof Error ? e.message : "Could not load employee activity"); }); return () => { active = false; }; }, [id]);
  return <RoleGate roles={["admin", "manager"]}><div className="space-y-6"><Link href="/employees" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">← Team directory</Link>
    {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}
    <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Employee activity</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">{employee?.name || "Loading employee…"}</h1><p className="mt-2 text-sm text-slate-500">{employee?.email} {employee && <span className="capitalize">· {employee.role}</span>}</p></header>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric label="Completed tasks" value={summary ? String(summary.tasks_completed) : "—"}/><Metric label="AI usage events" value={summary ? String(summary.ai_usage_events) : "—"}/><Metric label="Time saved" value={summary ? `${formatValue(summary.time_saved_minutes)} min` : "—"}/><Metric label="AI spend" value={summary ? formatValue(summary.ai_cost, "$ ") : "—"}/></div>
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-900">Tracked work</h2><p className="mt-1 text-xs text-slate-500">Task history, status, and recorded AI activity.</p></div>{tasks.length ? <div className="divide-y divide-slate-100">{tasks.map(task => <Link key={task.id} href={`/tasks/${task.id}`} className="flex items-center justify-between gap-3 px-5 py-4 hover:bg-slate-50"><div><p className="text-sm font-medium text-slate-900">{task.title}</p><p className="mt-1 text-xs text-slate-500">{task.category || "Uncategorized"}</p></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs capitalize text-slate-600">{task.status}</span></Link>)}</div> : <p className="px-5 py-10 text-center text-sm text-slate-500">No tracked tasks for this employee.</p>}</section>
    <p className="rounded-xl border border-indigo-100 bg-indigo-50/70 px-4 py-3 text-sm leading-6 text-indigo-900">AI cost: {summary ? formatValue(summary.ai_cost, "$ ") : "—"}. Estimated labor value: {summary ? formatValue(summary.estimated_value, "$ ") : "—"}. ROI: {summary ? (typeof summary.roi_percentage === "number" ? `${formatValue(summary.roi_percentage)}%` : summary.roi_percentage) : "—"}.</p>
  </div></RoleGate>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-semibold text-slate-900">{value}</p></div>; }
