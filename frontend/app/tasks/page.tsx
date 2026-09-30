"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, Task } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export default function TasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api.tasks().then(setTasks).catch(e => setError(e.message)); }, []);
  const completed = tasks.filter(task => task.status === "completed").length;
  return <div className="space-y-6">
    <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">{user?.role === "employee" ? "Your work" : "Operations"}</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-slate-900">Tasks</h1><p className="mt-2 text-sm text-slate-500">{user?.role === "employee" ? "Review your AI-assisted work and its measured outcomes." : "Review recorded work and outcome details across the workspace."}</p></header>
    <div className="grid gap-4 sm:grid-cols-3"><Metric label="Tasks" value={tasks.length}/><Metric label="Completed" value={completed}/><Metric label="In progress" value={tasks.length - completed}/></div>
    {error && <p role="alert" className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">Could not load tasks. {error}</p>}
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-900">Recent tasks</h2></div>{tasks.length ? <div className="divide-y divide-slate-100">{tasks.map(task => <Link key={task.id} href={`/tasks/${task.id}`} className="flex flex-col gap-2 px-5 py-4 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"><div><p className="font-medium text-slate-900">{task.title}</p><p className="mt-1 text-xs text-slate-500">{task.category || "Uncategorized"}{user?.role !== "employee" && ` · Employee ${task.employee_id.slice(0, 8)}`}</p></div><span className={`w-fit rounded-full px-2.5 py-1 text-xs font-medium ${task.status === "completed" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{task.status}</span></Link>)}</div> : !error && <p className="px-5 py-12 text-center text-sm text-slate-500">No tasks recorded yet.</p>}</section>
  </div>;
}

function Metric({ label, value }: { label: string; value: number }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p></div>; }
