import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200",
  in_progress: "bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-200",
  completed: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  failed: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
};

export default async function TasksPage() {
  const tasks = await api.tasks().catch(() => []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Work tracking</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">Tasks</h1>
        <p className="mt-2 text-sm text-slate-500">Review task progress, AI usage, and estimated return.</p></div>
        <span className="inline-flex w-fit items-center rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm">{tasks.length} {tasks.length === 1 ? "task" : "tasks"}</span>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-900/[0.025]">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="px-4 py-2">Title</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Baseline (min)</th>
              <th className="px-4 py-2">Actual (min)</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} className="border-t border-slate-100">
                <td className="px-5 py-4 font-medium text-slate-900">{t.title}</td>
                <td className="px-5 py-4 text-slate-500">{t.category ?? "—"}</td>
                <td className="px-5 py-4 text-slate-500">{t.baseline_minutes ?? "N/A"}</td>
                <td className="px-5 py-4 text-slate-500">
                  {t.actual_minutes !== null ? t.actual_minutes.toFixed(1) : "N/A"}
                </td>
                <td className="px-5 py-4">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[t.status] ?? ""}`}>
                    {t.status}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  <Link href={`/tasks/${t.id}`} className="inline-flex items-center rounded-lg px-2.5 py-1.5 font-medium text-indigo-600 transition hover:bg-indigo-50 hover:text-indigo-800">
                    View details <span className="ml-1">→</span>
                  </Link>
                </td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-14 text-center">
                  <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">✦</span>
                  <span className="mt-3 block font-medium text-slate-700">No tasks to show yet</span>
                  <span className="mt-1 block text-sm text-slate-400">Tasks will appear here when they are started.</span>
                </td>
              </tr>
            )}
          </tbody>
        </table></div>
      </div>
    </div>
  );
}
