"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import KpiCard from "@/components/KpiCard";
import { useAuth } from "@/components/AuthProvider";
import { api, EmployeeDashboard, formatValue, ManagementDashboard, Task } from "@/lib/api";
import { BarChartCard, PieChartCard } from "@/components/DashboardCharts";

export default function DashboardPage() {
  const { user } = useAuth();
  const [management, setManagement] = useState<ManagementDashboard | null>(null);
  const [employee, setEmployee] = useState<EmployeeDashboard | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    if (user?.role === "employee") {
      Promise.all([api.employeeDashboard(user.id), api.tasks({ employee_id: user.id })])
        .then(([dashboard, taskList]) => { if (active) { setEmployee(dashboard); setTasks(taskList.slice(0, 5)); } })
        .catch(e => { if (active) setError(e instanceof Error ? e.message : "Could not load your dashboard"); });
    } else if (user) {
      api.managementDashboard().then(data => { if (active) setManagement(data); })
        .catch(e => { if (active) setError(e instanceof Error ? e.message : "Could not load analytics"); });
    }
    return () => { active = false; };
  }, [user]);

  if (!user) return null;
  if (error) return <div role="alert" className="rounded-2xl border border-rose-200 bg-white p-6 text-sm text-rose-800">{error}</div>;
  if (user.role === "employee") return <EmployeeHome userName={user.name} data={employee} tasks={tasks} />;
  return <ManagerHome data={management} />;
}

function EmployeeHome({ userName, data, tasks }: { userName: string; data: EmployeeDashboard | null; tasks: Task[] }) {
  const firstName = userName.trim().split(/\s+/)[0];
  return <div className="space-y-7">
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-indigo-800 px-6 py-8 text-white shadow-lg shadow-indigo-950/10 sm:px-9 sm:py-10"><div className="absolute -right-12 -top-20 h-64 w-64 rounded-full bg-indigo-400/20 blur-3xl"/><div className="relative"><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-200">Employee workspace</p><h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Welcome back, {firstName}.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-100/80">Your tasks and AI activity in one place. Analyze prompts, choose a suitable model, and connect supported work accounts.</p><div className="mt-6 flex flex-wrap gap-3"><Link href="/prompt-intelligence" className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-indigo-800 transition hover:bg-indigo-50">Analyze a prompt</Link><Link href="/agent-optimization" className="rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/15">Optimize a task</Link></div></div></section>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><KpiCard label="Completed tasks" value={data ? String(data.tasks_completed) : "—"} source="observed"/><KpiCard label="AI requests" value={data ? String(data.ai_usage_events) : "—"} source="observed"/><KpiCard label="Time saved" value={data ? `${formatValue(data.time_saved_minutes)} min` : "—"} source="observed"/><KpiCard label="Your AI spend" value={data ? formatValue(data.ai_cost, "$") : "—"} source={typeof data?.ai_cost === "number" ? "connector" : "unavailable"}/></div>
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]"><section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-900">Recent tasks</h2><p className="mt-0.5 text-xs text-slate-500">Your latest tracked work</p></div><Link href="/tasks" className="text-xs font-semibold text-indigo-600 hover:text-indigo-800">All tasks →</Link></div>{tasks.length ? <div className="divide-y divide-slate-100">{tasks.map(task => <Link key={task.id} href={`/tasks/${task.id}`} className="flex items-center justify-between gap-4 px-5 py-4 transition hover:bg-slate-50"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">{task.title}</p><p className="mt-1 text-xs capitalize text-slate-400">{task.category ?? "General"}</p></div><span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium capitalize text-slate-600">{task.status.replace("_", " ")}</span></Link>)}</div> : <p className="px-5 py-10 text-center text-sm text-slate-400">Your tasks will show up here.</p>}</section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Your tools</p><div className="mt-3 space-y-2"><ToolLink href="/prompt-intelligence" title="Prompt analyzer" text="Improve clarity and completeness."/><ToolLink href="/agent-optimization" title="Agent optimizer" text="Find a model that fits the task."/><ToolLink href="/connectors" title="Connected accounts" text="Link supported work tools."/></div></section>
    </div>
  </div>;
}

function ToolLink({ href, title, text }: { href: string; title: string; text: string }) {
  return <Link href={href} className="group flex items-center justify-between rounded-xl border border-slate-100 p-3.5 transition hover:border-indigo-100 hover:bg-indigo-50/40"><span><span className="block text-sm font-semibold text-slate-800">{title}</span><span className="mt-0.5 block text-xs text-slate-500">{text}</span></span><span className="text-lg text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-500">→</span></Link>;
}

function ManagerHome({ data: d }: { data: ManagementDashboard | null }) {
  if (!d) return <div className="flex min-h-80 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" aria-label="Loading analytics"/></div>;
  return <div className="space-y-7">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Management overview</p><h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">AI usage & business impact</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-500">Review observed usage, team adoption, and estimated ROI. Labor value uses configured assumptions and is not causal proof of productivity improvement.</p></div><span className="inline-flex items-center gap-2 self-start rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 sm:self-auto"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500"/>Live analytics</span></div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"><KpiCard label="AI spend" value={formatValue(d.ai_spend.value,"$")} source={d.ai_spend.source} note={d.ai_spend.note}/><KpiCard label="AI-assisted tasks" value={`${d.ai_assisted_tasks} / ${d.total_tasks}`} source="observed"/><KpiCard label="Time saved" value={`${formatValue(d.time_saved_minutes.value)} min`} source="observed"/><KpiCard label="Estimated business value" value={formatValue(d.estimated_business_value.value,"$")} source="estimated"/><KpiCard label="Net estimated value" value={formatValue(d.net_estimated_value.value,"$")} source={d.net_estimated_value.source}/><KpiCard label="Estimated ROI" value={typeof d.aggregate_roi_percentage.value === "number" ? `${formatValue(d.aggregate_roi_percentage.value)}%` : "N/A"} source={d.aggregate_roi_percentage.source}/></div>
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3"><KpiCard label="AI adoption" value={`${d.ai_adoption_pct}%`} source="observed"/><KpiCard label="Cost per AI-assisted task" value={formatValue(d.cost_per_ai_assisted_task,"$")} source={typeof d.cost_per_ai_assisted_task === "number" ? "connector" : "unavailable"}/><KpiCard label="ROI multiple" value={typeof d.roi_multiple.value === "number" ? `${formatValue(d.roi_multiple.value)}x` : "N/A"} source={typeof d.roi_multiple.value === "number" ? "estimated" : "unavailable"}/></div>
    {d.tasks_missing_cost_data > 0 && <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">{d.tasks_missing_cost_data} tasks with calculated labor value have no AI cost data and are excluded from aggregate ROI.</div>}
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2"><BarChartCard title="Time saved by department (minutes)" data={d.department_stats.map(s=>({name:s.department,value:Math.round(s.time_saved_minutes)}))}/><BarChartCard title="AI adoption by department (%)" data={d.department_stats.map(s=>({name:s.department,value:s.ai_adoption_pct}))}/></div>
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2"><PieChartCard title="AI usage by provider" data={Object.entries(d.provider_stats).map(([name,s])=>({name,value:s.events}))}/><section className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 className="font-semibold text-slate-900">Department breakdown</h2><div className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead><tr><th className="pb-3 text-left">Department</th><th className="pb-3 text-left">People</th><th className="pb-3 text-left">Tasks</th><th className="pb-3 text-left">Adoption</th><th className="pb-3 text-left">Spend</th></tr></thead><tbody>{d.department_stats.map(s=><tr key={s.department_id} className="border-t border-slate-100"><td className="py-3 font-medium text-slate-800">{s.department}</td><td className="py-3 text-slate-500">{s.employees}</td><td className="py-3 text-slate-500">{s.tasks}</td><td className="py-3 text-slate-500">{s.ai_adoption_pct}%</td><td className="py-3 text-slate-500">{formatValue(s.ai_spend,"$")}</td></tr>)}</tbody></table></div><Link href="/employees" className="mt-4 inline-flex text-xs font-semibold text-indigo-600 hover:text-indigo-800">Manage employees →</Link></section></div>
  </div>;
}
