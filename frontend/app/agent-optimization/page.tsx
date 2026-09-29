"use client";

import { FormEvent, useEffect, useState } from "react";
import { AgentAnalytics, AgentDecision, api } from "@/lib/api";

const fieldClass = "mt-2 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-100";

function SparkIcon() {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" className="h-5 w-5"><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/><path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z" fill="currentColor"/></svg>;
}

function Metric({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return <div className="rounded-2xl border border-slate-100 bg-white p-4">
    <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
    <p className="mt-2 text-xl font-semibold tracking-tight text-slate-900">{value}</p>
    {detail && <p className="mt-1 text-xs text-slate-500">{detail}</p>}
  </div>;
}

export default function AgentOptimizationPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [quality, setQuality] = useState(80);
  const [actualQuality, setActualQuality] = useState("");
  const [actualLatency, setActualLatency] = useState("");
  const [actualInputTokens, setActualInputTokens] = useState("");
  const [actualOutputTokens, setActualOutputTokens] = useState("");
  const [actualCost, setActualCost] = useState("");
  const [decision, setDecision] = useState<AgentDecision | null>(null);
  const [analytics, setAnalytics] = useState<AgentAnalytics | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refreshAnalytics() {
    try { setAnalytics(await api.agentAnalytics()); }
    catch { setAnalytics(null); }
  }
  useEffect(() => {
    let active = true;
    api.agentAnalytics().then(value => { if (active) setAnalytics(value); }).catch(() => { if (active) setAnalytics(null); });
    return () => { active = false; };
  }, []);

  async function recommend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError(""); setDecision(null);
    try {
      const next = await api.optimizeAgent({ title: title.trim(), description: description.trim(), required_quality: quality });
      setDecision(next);
      await refreshAnalytics();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not recommend an agent");
    } finally { setBusy(false); }
  }

  async function record(outcome: "success" | "failed") {
    if (!decision) return;
    if (!actualQuality) { setError("Add the measured quality score before saving this result."); return; }
    setBusy(true); setError("");
    try {
      const updated = await api.recordAgentResult(decision.id, {
        outcome,
        actual_quality: Number(actualQuality),
        actual_latency_ms: actualLatency ? Number(actualLatency) : undefined,
        actual_input_tokens: actualInputTokens ? Number(actualInputTokens) : undefined,
        actual_output_tokens: actualOutputTokens ? Number(actualOutputTokens) : undefined,
        actual_cost: actualCost ? Number(actualCost) : undefined,
        rework_required: outcome === "failed",
      });
      setDecision(updated);
      await refreshAnalytics();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not record this result");
    } finally { setBusy(false); }
  }

  const allRequirementsMet = decision?.rationale?.all_requirements_met !== false;
  const actualTokenTotal = decision?.actual_input_tokens != null && decision.actual_output_tokens != null
    ? decision.actual_input_tokens + decision.actual_output_tokens : null;

  return <div className="mx-auto max-w-6xl space-y-7 pb-10">
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-indigo-800 px-6 py-8 text-white shadow-lg shadow-indigo-950/10 sm:px-9 sm:py-10">
      <div className="absolute -right-16 -top-24 h-72 w-72 rounded-full bg-indigo-400/20 blur-3xl" />
      <div className="absolute bottom-0 right-1/3 h-36 w-36 rounded-full bg-violet-400/10 blur-2xl" />
      <div className="relative flex flex-col justify-between gap-8 lg:flex-row lg:items-end">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-indigo-100">
            <SparkIcon /> Cost-aware routing
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight sm:text-4xl">The right model for every task.</h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-indigo-100/80 sm:text-base">
            Compare task requirements with model capability, cost, speed, and recorded outcomes. Each recommendation improves as your team logs results.
          </p>
        </div>
        <div className="grid min-w-64 grid-cols-2 gap-3">
          <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur-sm"><p className="text-xs text-indigo-100/70">Routes evaluated</p><p className="mt-1 text-2xl font-semibold">{analytics?.recommendations ?? "—"}</p></div>
          <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur-sm"><p className="text-xs text-indigo-100/70">Results learned</p><p className="mt-1 text-2xl font-semibold">{analytics?.results_recorded ?? "—"}</p></div>
        </div>
      </div>
    </section>

    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.55fr)_minmax(280px,0.8fr)]">
      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5 sm:px-7">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-sm font-semibold text-indigo-700">01</span>
            <div><h2 className="font-semibold text-slate-900">Describe the task</h2><p className="mt-0.5 text-xs text-slate-500">Set the quality bar and let the optimizer compare eligible models.</p></div>
          </div>
        </div>
        <form onSubmit={recommend} className="space-y-5 px-6 py-6 sm:px-7">
          <label className="block text-sm font-medium text-slate-700">Task name
            <input required maxLength={240} value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Add validation to the billing API" className={fieldClass} />
          </label>
          <label className="block text-sm font-medium text-slate-700">Context <span className="font-normal text-slate-400">(optional)</span>
            <textarea value={description} onChange={e => setDescription(e.target.value)} rows={4} placeholder="Add relevant requirements, constraints, or expected output…" className={`${fieldClass} resize-y`} />
          </label>
          <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-4 sm:p-5">
            <div className="flex items-start justify-between gap-3">
              <div><p className="text-sm font-medium text-slate-700">Minimum quality target</p><p className="mt-1 text-xs text-slate-500">Higher targets may require a more capable model.</p></div>
              <span className="rounded-lg bg-white px-2.5 py-1 text-sm font-semibold text-indigo-700 shadow-sm">{quality}<span className="text-xs font-medium text-slate-400"> / 100</span></span>
            </div>
            <input aria-label="Minimum quality target" type="range" min={60} max={96} value={quality} onChange={e => setQuality(Number(e.target.value))} className="mt-4 h-2 w-full cursor-pointer accent-indigo-600" />
            <div className="mt-2 flex justify-between text-[11px] text-slate-400"><span>Cost focused</span><span>Quality focused</span></div>
          </div>
          {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
          <button type="submit" disabled={!title.trim() || busy} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm shadow-indigo-600/20 transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:min-w-52">
            {busy ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Finding a fit…</> : <><SparkIcon /> Get recommendation</>}
          </button>
        </form>

        {decision && <div className="border-t border-slate-100 bg-slate-50/60 p-5 sm:p-7">
          <div className={`rounded-2xl border bg-white p-5 shadow-sm sm:p-6 ${allRequirementsMet ? "border-emerald-200" : "border-amber-200"}`}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${allRequirementsMet ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}><SparkIcon /></span>
                <div><p className="text-xs font-medium uppercase tracking-wide text-slate-400">Recommended model</p><h3 className="mt-0.5 text-lg font-semibold text-slate-900">{decision.selected_model}</h3><p className="text-xs capitalize text-slate-500">{decision.selected_provider} · {decision.task_type} · {decision.complexity} complexity</p></div>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${allRequirementsMet ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-800"}`}>{allRequirementsMet ? "Meets requirements" : "Best available · review limits"}</span>
            </div>

            {!allRequirementsMet && <p className="mt-4 rounded-xl bg-amber-50 px-3.5 py-3 text-sm leading-5 text-amber-900">No catalog model is predicted to meet every requested constraint. Review the quality and latency estimates before using this recommendation.</p>}
            <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Metric label="Predicted quality" value={`${decision.predicted_quality}/100`} detail={`Target ${decision.required_quality}`} />
              <Metric label="Estimated cost" value={decision.predicted_cost != null ? `$${decision.predicted_cost.toFixed(6)}` : "N/A"} detail="Based on token estimate" />
              <Metric label="Estimated tokens" value={((decision.predicted_input_tokens ?? 0) + (decision.predicted_output_tokens ?? 0)).toLocaleString()} detail="Input + output" />
              <Metric label="Response time" value={decision.predicted_latency_ms != null ? `${(decision.predicted_latency_ms / 1000).toFixed(1)}s` : "N/A"} detail={`${Math.round(decision.confidence * 100)}% historical confidence`} />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1.5"><span className={`h-1.5 w-1.5 rounded-full ${decision.verification_required ? "bg-amber-500" : "bg-slate-300"}`} />{decision.verification_required ? "Verification recommended" : "No extra verification suggested"}</span>
              <span>{Number(decision.rationale?.historical_samples ?? 0)} comparable results in history</span>
            </div>
          </div>

          <details className="group mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-medium text-slate-700 marker:hidden">
              <span>Log this task’s actual result</span><span className="text-lg text-slate-400 transition group-open:rotate-45">+</span>
            </summary>
            <div className="border-t border-slate-100 px-5 py-5">
              {decision.outcome && <p className="mb-4 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800">Result saved: {decision.outcome}{actualTokenTotal != null ? ` · ${actualTokenTotal.toLocaleString()} tokens` : ""}</p>}
              <p className="mb-4 text-xs leading-5 text-slate-500">Recorded outcomes tune future recommendations for similar tasks. Enter observed values; leave unavailable measurements blank.</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <label className="text-xs font-medium text-slate-600">Quality score<input type="number" min="0" max="100" value={actualQuality} onChange={e => setActualQuality(e.target.value)} placeholder="0–100" className={fieldClass} /></label>
                <label className="text-xs font-medium text-slate-600">Response time<input type="number" min="0" value={actualLatency} onChange={e => setActualLatency(e.target.value)} placeholder="Milliseconds" className={fieldClass} /></label>
                <label className="text-xs font-medium text-slate-600">Actual cost<input type="number" min="0" step="any" value={actualCost} onChange={e => setActualCost(e.target.value)} placeholder="USD" className={fieldClass} /></label>
                <label className="text-xs font-medium text-slate-600">Input tokens<input type="number" min="0" value={actualInputTokens} onChange={e => setActualInputTokens(e.target.value)} placeholder="Observed count" className={fieldClass} /></label>
                <label className="text-xs font-medium text-slate-600">Output tokens<input type="number" min="0" value={actualOutputTokens} onChange={e => setActualOutputTokens(e.target.value)} placeholder="Observed count" className={fieldClass} /></label>
              </div>
              {error && <p role="alert" className="mt-3 text-xs text-rose-600">{error}</p>}
              <div className="mt-4 flex flex-wrap gap-2">
                <button disabled={busy} onClick={() => void record("success")} className="rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50">Save successful result</button>
                <button disabled={busy} onClick={() => void record("failed")} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50">Save with rework needed</button>
              </div>
            </div>
          </details>
        </div>}
      </section>

      <aside className="space-y-5">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center justify-between"><div><p className="text-xs font-medium uppercase tracking-wide text-slate-400">Your optimizer</p><h2 className="mt-1 font-semibold text-slate-900">Learning over time</h2></div><span className="rounded-xl bg-violet-50 p-2.5 text-violet-700"><SparkIcon /></span></div>
          <div className="mt-5 space-y-4">
            <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Actual AI cost logged</span><span className="text-sm font-semibold text-slate-900">{analytics ? `$${Number(analytics.actual_cost).toFixed(5)}` : "—"}</span></div>
            <div className="h-px bg-slate-100" />
            <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Average quality observed</span><span className="text-sm font-semibold text-slate-900">{analytics?.average_actual_quality != null ? `${Number(analytics.average_actual_quality).toFixed(1)} / 100` : "—"}</span></div>
            <div className="h-px bg-slate-100" />
            <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Models compared</span><span className="text-sm font-semibold text-slate-900">{analytics ? Object.keys(analytics.models).length : "—"}</span></div>
          </div>
          {analytics && analytics.recommendations === 0 && <div className="mt-5 rounded-xl bg-slate-50 p-3.5 text-xs leading-5 text-slate-500">No history yet. Generate recommendations and log real outcomes to calibrate future choices.</div>}
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <h2 className="font-semibold text-slate-900">How selection works</h2>
          <ol className="mt-4 space-y-4">
            {[
              ["01", "Estimate task needs", "Task type and complexity set the initial quality and token estimates."],
              ["02", "Filter capable models", "Models below the quality bar or outside the latency limit are excluded."],
              ["03", "Choose by cost", "The least expensive eligible option is recommended."],
              ["04", "Learn from outcomes", "Observed quality, usage, and rework inform later routing."],
            ].map(([number, heading, copy]) => <li key={number} className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-[10px] font-semibold text-slate-500">{number}</span><div><h3 className="text-sm font-medium text-slate-800">{heading}</h3><p className="mt-1 text-xs leading-5 text-slate-500">{copy}</p></div></li>)}
          </ol>
          <p className="mt-5 rounded-xl border border-indigo-100 bg-indigo-50/60 p-3.5 text-[11px] leading-5 text-indigo-800">Model quality and latency are estimates from the configured catalog. Recommendations are advisory; task creation records one automatically.</p>
        </section>
      </aside>
    </div>
  </div>;
}
