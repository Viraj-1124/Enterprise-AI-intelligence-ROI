import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-600",
  in_progress: "bg-blue-50 text-blue-700",
  completed: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-700",
};

export default async function TasksPage() {
  const tasks = await api.tasks().catch(() => []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Tasks</h1>
        <p className="mt-1 text-sm text-gray-500">
          Every task started through <code className="rounded bg-gray-100 px-1">POST /api/tasks/start</code>, most
          recent first.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
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
              <tr key={t.id} className="border-t border-gray-100">
                <td className="px-4 py-2 font-medium text-gray-900">{t.title}</td>
                <td className="px-4 py-2 text-gray-600">{t.category ?? "—"}</td>
                <td className="px-4 py-2 text-gray-600">{t.baseline_minutes ?? "N/A"}</td>
                <td className="px-4 py-2 text-gray-600">
                  {t.actual_minutes !== null ? t.actual_minutes.toFixed(1) : "N/A"}
                </td>
                <td className="px-4 py-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[t.status] ?? ""}`}>
                    {t.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-right">
                  <Link href={`/tasks/${t.id}`} className="text-indigo-600 hover:underline">
                    View ROI →
                  </Link>
                </td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  No tasks yet. Start one via <code>POST /api/tasks/start</code>.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
