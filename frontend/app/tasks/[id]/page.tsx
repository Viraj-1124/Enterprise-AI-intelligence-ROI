import { notFound } from "next/navigation";
import { api, formatValue } from "@/lib/api";
import ProvenanceBadge from "@/components/ProvenanceBadge";

export const dynamic = "force-dynamic";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] sm:p-6">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      <div className="mt-3 space-y-2">{children}</div>
    </div>
  );
}

function Row({ label, value, source }: { label: string; value: string; source?: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="flex items-center gap-2 font-medium text-slate-900">
        {value}
        {source && <ProvenanceBadge source={source} />}
      </span>
    </div>
  );
}

export default async function TaskDetailPage({ params }: PageProps<"/tasks/[id]">) {
  const { id } = await params;

  const task = await api.task(id).catch(() => null);
  if (!task) notFound();

  const [roi, aiEvents, outcome] = await Promise.all([
    api.taskROI(id),
    api.taskAIEvents(id).catch(() => []),
    api.taskOutcome(id),
  ]);

  const aiCostAvailable = roi && roi.ai_cost !== null;

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Task report</p>
        <h1 className="mt-1 text-2xl font-semibold text-slate-900 sm:text-3xl">{task.title}</h1>
        <p className="mt-2 text-sm text-slate-500">{task.category ?? "Uncategorized"} <span className="mx-1 text-slate-300">·</span> Task ID <span className="font-mono text-xs">{task.id}</span></p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Section title="Task Information">
          <Row label="Status" value={task.status} />
          <Row label="Started" value={task.started_at ? new Date(task.started_at).toLocaleString() : "N/A"} source={task.started_at ? "observed" : undefined} />
          <Row label="Completed" value={task.completed_at ? new Date(task.completed_at).toLocaleString() : "N/A"} source={task.completed_at ? "observed" : undefined} />
          <Row label="Duration" value={task.actual_minutes !== null ? `${task.actual_minutes.toFixed(1)} min` : "N/A"} source={task.actual_minutes !== null ? "observed" : undefined} />
        </Section>

        <Section title="AI Investment">
          {aiEvents.length === 0 ? (
            <p className="text-sm text-gray-400">No AI usage recorded for this task.</p>
          ) : (
            aiEvents.map((e) => (
              <div key={e.id} className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{e.provider}{e.model ? ` · ${e.model}` : ""}</span>
                  <ProvenanceBadge source={e.source} />
                </div>
                <div className="mt-1 text-gray-500">
                  Tokens: {e.total_tokens ?? "N/A"} · Cost: {formatValue(e.cost, "$")}
                </div>
              </div>
            ))
          )}
        </Section>

        <Section title="Work Outcome">
          <Row label="Manual baseline" value={task.baseline_minutes !== null ? `${task.baseline_minutes} min` : "N/A"} source={task.baseline_minutes !== null ? "estimated" : undefined} />
          <Row label="AI-assisted time" value={task.actual_minutes !== null ? `${task.actual_minutes.toFixed(1)} min` : "N/A"} source={task.actual_minutes !== null ? "observed" : undefined} />
          <Row label="Time saved" value={roi?.time_saved_minutes != null ? `${roi.time_saved_minutes.toFixed(1)} min` : "N/A"} source={roi?.time_saved_minutes != null ? "estimated" : undefined} />
          <Row label="Time saved %" value={roi?.time_saved_percentage != null ? `${roi.time_saved_percentage.toFixed(1)}%` : "N/A"} />
          {outcome && (
            <>
              <Row label="Files changed" value={String(outcome.files_changed)} source="observed" />
              <Row label="Commits" value={String(outcome.commits)} source="observed" />
              <Row label="Tests" value={`${outcome.tests_passed} / ${outcome.tests_run} passed`} source="observed" />
              <Row label="Build" value={outcome.build_passed === null ? "N/A" : outcome.build_passed ? "Passed" : "Failed"} source={outcome.build_passed !== null ? "observed" : undefined} />
            </>
          )}
        </Section>

        <Section title="Business Value">
          <Row label="Estimated labor value" value={formatValue(roi?.estimated_labor_value, "$")} source={roi?.estimated_labor_value != null ? "estimated" : undefined} />
          <Row label="AI cost" value={formatValue(roi?.ai_cost, "$")} source={aiCostAvailable ? "connector" : "unavailable"} />
          <Row label="Net estimated value" value={formatValue(roi?.net_value, "$")} source={roi?.net_value != null ? "estimated" : undefined} />
        </Section>
      </div>

      <Section title="ROI">
        {!roi || roi.calculation_status === "unavailable" ? (
          <p className="text-sm text-gray-500">
            ROI cannot currently be calculated — a manual baseline and/or completion time is missing.
          </p>
        ) : !aiCostAvailable ? (
          <p className="text-sm text-amber-700">
            AI cost unavailable from connected sources. ROI cannot currently be calculated, though the
            estimated labor value from time saved is shown above.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">ROI %</p>
              <p className="text-2xl font-semibold text-gray-900">{formatValue(roi.roi_percentage)}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">ROI multiple</p>
              <p className="text-2xl font-semibold text-gray-900">{formatValue(roi.roi_multiple)}x</p>
            </div>
          </div>
        )}
      </Section>

      {roi && (
        <Section title="Calculation Breakdown">
          <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-xs text-gray-700">
{`Manual baseline: ${task.baseline_minutes ?? "N/A"} min
Actual time: ${task.actual_minutes?.toFixed(1) ?? "N/A"} min

Time saved:
${task.baseline_minutes ?? "?"} - ${task.actual_minutes?.toFixed(1) ?? "?"} = ${roi.time_saved_minutes?.toFixed(1) ?? "N/A"} min

Estimated labor value:
(${roi.time_saved_minutes?.toFixed(1) ?? "N/A"} / 60) × hourly_cost = ${formatValue(roi.estimated_labor_value, "$")}

AI cost: ${formatValue(roi.ai_cost, "$")}${!aiCostAvailable ? "  (unavailable — ROI not calculated)" : ""}
${aiCostAvailable ? `
Net value:
${formatValue(roi.estimated_labor_value, "$")} - ${formatValue(roi.ai_cost, "$")} = ${formatValue(roi.net_value, "$")}

ROI %:
((${formatValue(roi.estimated_labor_value, "$")} - ${formatValue(roi.ai_cost, "$")}) / ${formatValue(roi.ai_cost, "$")}) × 100 = ${formatValue(roi.roi_percentage)}%` : ""}`}
          </pre>
        </Section>
      )}
    </div>
  );
}
