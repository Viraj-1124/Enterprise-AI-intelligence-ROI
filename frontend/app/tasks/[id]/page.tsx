"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, formatValue, Task, ROI, AIUsageEvent, TaskOutcome } from "@/lib/api";

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [roi, setRoi] = useState<ROI | null>(null);
  const [events, setEvents] = useState<AIUsageEvent[]>([]);
  const [outcome, setOutcome] = useState<TaskOutcome | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { let active = true; Promise.all([api.task(id), api.taskROI(id), api.taskAIEvents(id).catch(() => []), api.taskOutcome(id)]).then(([t, r, e, o]) => { if (active) { setTask(t); setRoi(r); setEvents(e); setOutcome(o); } }).catch(e => { if (active) setError(e instanceof Error ? e.message : "Could not load task"); }); return () => { active = false; }; }, [id]);
  if (error) return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700"><p className="font-semibold">Unable to load this task</p><p className="mt-1">{error}</p><Link className="mt-4 inline-block font-medium underline" href="/tasks">Back to tasks</Link></div>;
  if (!task) return <div className="py-20 text-center text-sm text-slate-500">Loading task report…</div>;
  const costAvailable = roi?.ai_cost != null;
  return <div className="space-y-6"><div><Link href="/tasks" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">← All tasks</Link><p className="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Task report</p><h1 className="mt-1 text-3xl font-semibold text-slate-900">{task.title}</h1><p className="mt-2 text-sm text-slate-500">{task.category || "Uncategorized"} · <span className="font-mono text-xs">{task.id}</span></p></div>
    <div className="grid gap-5 lg:grid-cols-2"><Section title="Task information"><Row label="Status" value={task.status}/><Row label="Started" value={task.started_at ? new Date(task.started_at).toLocaleString() : "N/A"}/><Row label="Completed" value={task.completed_at ? new Date(task.completed_at).toLocaleString() : "N/A"}/><Row label="Duration" value={task.actual_minutes != null ? `${task.actual_minutes.toFixed(1)} min` : "N/A"}/></Section>
    <Section title="AI investment">{events.length ? events.map(e => <div key={e.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4"><p className="font-medium text-slate-900">{e.provider}{e.model ? ` · ${e.model}` : ""}</p><p className="mt-1 text-sm text-slate-500">{e.total_tokens ?? "N/A"} tokens · {formatValue(e.cost, "$ ")}</p></div>) : <p className="text-sm text-slate-500">No AI usage recorded for this task.</p>}</Section>
    <Section title="Work outcome"><Row label="Manual baseline" value={task.baseline_minutes != null ? `${task.baseline_minutes} min` : "N/A"}/><Row label="AI-assisted time" value={task.actual_minutes != null ? `${task.actual_minutes.toFixed(1)} min` : "N/A"}/><Row label="Time saved" value={roi?.time_saved_minutes != null ? `${roi.time_saved_minutes.toFixed(1)} min` : "N/A"}/>{outcome && <><Row label="Files changed" value={String(outcome.files_changed)}/><Row label="Commits" value={String(outcome.commits)}/><Row label="Tests passed" value={`${outcome.tests_passed} / ${outcome.tests_run}`}/></>}</Section>
    <Section title="Business value"><Row label="Estimated labor value" value={formatValue(roi?.estimated_labor_value, "$ ")}/><Row label="AI cost" value={formatValue(roi?.ai_cost, "$ ")}/><Row label="Net estimated value" value={formatValue(roi?.net_value, "$ ")}/></Section></div>
    <Section title="ROI">{!roi || roi.calculation_status === "unavailable" ? <p className="text-sm text-slate-500">ROI cannot be calculated yet because task timing or baseline data is missing.</p> : !costAvailable ? <p className="text-sm text-amber-700">AI cost is unavailable from connected sources. Estimated labor value is shown above.</p> : <div className="grid grid-cols-2 gap-4"><div><p className="text-xs text-slate-500">ROI</p><p className="mt-1 text-2xl font-semibold text-slate-900">{formatValue(roi.roi_percentage)}%</p></div><div><p className="text-xs text-slate-500">ROI multiple</p><p className="mt-1 text-2xl font-semibold text-slate-900">{formatValue(roi.roi_multiple)}×</p></div></div>}</Section>
  </div>;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) { return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h2 className="text-sm font-semibold text-slate-800">{title}</h2><div className="mt-4 space-y-3">{children}</div></section>; }
function Row({ label, value }: { label: string; value: string }) { return <div className="flex items-center justify-between gap-3 text-sm"><span className="text-slate-500">{label}</span><span className="text-right font-medium text-slate-900">{value}</span></div>; }
