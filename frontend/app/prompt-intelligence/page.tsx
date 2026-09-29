"use client";

import { FormEvent, useState } from "react";
import { api, PromptAnalysis } from "@/lib/api";

const LABELS: Record<string, string> = { clarity: "Clarity", context: "Context", specificity: "Specificity", output_requirements: "Output requirements", ambiguity: "Clarity of intent", completeness: "Completeness" };

export default function PromptIntelligencePage() {
  const [prompt, setPrompt] = useState("Build an API for users.");
  const [result, setResult] = useState<PromptAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true); setError(null);
    try { setResult(await api.analyzePrompt(prompt)); }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to analyze prompt"); }
    finally { setLoading(false); }
  }

  const average = result ? Math.round(Object.values(result.scores).reduce((sum, n) => sum + n, 0) / Math.max(1, Object.values(result.scores).length)) : 0;

  return <div className="mx-auto max-w-6xl space-y-7 pb-10">
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-violet-950 via-indigo-900 to-indigo-700 px-6 py-8 text-white shadow-lg shadow-indigo-950/10 sm:px-9 sm:py-10">
      <div className="absolute -right-12 -top-20 h-64 w-64 rounded-full bg-fuchsia-400/15 blur-3xl" />
      <div className="relative max-w-2xl"><span className="inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-medium text-violet-100">Prompt quality assistant</span><h1 className="mt-5 text-3xl font-semibold tracking-tight sm:text-4xl">Turn a rough idea into a clear brief.</h1><p className="mt-3 text-sm leading-6 text-indigo-100/80 sm:text-base">Spot missing context, requirements, and edge cases before work begins. The analysis is deterministic and rule based.</p></div>
    </section>

    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(300px,0.7fr)]">
      <form onSubmit={analyze} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
        <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-50 text-sm font-semibold text-violet-700">01</span><div><h2 className="font-semibold text-slate-900">Your prompt</h2><p className="text-xs text-slate-500">Be as specific as you can; the analyzer will flag gaps.</p></div></div>
        <textarea aria-label="Prompt to analyze" className="mt-5 min-h-48 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50/60 p-4 text-sm leading-6 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-indigo-400 focus:bg-white focus:ring-4 focus:ring-indigo-100" rows={7} placeholder="Describe what you want to accomplish…" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
        <div className="mt-2 flex justify-between text-xs text-slate-400"><span>Include the output, constraints, and edge cases</span><span>{prompt.trim().split(/\s+/).filter(Boolean).length} words</span></div>
        {error && <p role="alert" className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <button type="submit" disabled={loading || prompt.trim().length === 0} className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto sm:min-w-48">{loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Reviewing prompt…</> : "Analyze prompt"}</button>
      </form>

      <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">A useful prompt includes</p><h2 className="mt-1 font-semibold text-slate-900">Five ingredients</h2>
        <ul className="mt-5 space-y-4">{[["01", "Context", "What is being built and why?"], ["02", "Specifics", "Which tools, data, or requirements apply?"], ["03", "Output", "What should the finished result look like?"], ["04", "Constraints", "What limits or rules must be respected?"], ["05", "Edge cases", "How should failures and unusual inputs behave?"]].map(([n, title, help]) => <li key={n} className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-[10px] font-semibold text-slate-500">{n}</span><span><span className="block text-sm font-medium text-slate-800">{title}</span><span className="mt-0.5 block text-xs leading-5 text-slate-500">{help}</span></span></li>)}</ul>
        <p className="mt-5 rounded-xl border border-violet-100 bg-violet-50/70 p-3 text-xs leading-5 text-violet-800">Your prompt is checked with local rules. No external model call is made.</p>
      </aside>
    </div>

    {result && <section className="space-y-4">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-indigo-600">Analysis complete</p><h2 className="mt-1 text-xl font-semibold text-slate-900">Here’s how your prompt reads</h2></div><span className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 shadow-sm">Average prompt score <strong className="ml-1 text-slate-900">{average}%</strong></span></div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><div className="flex items-center justify-between"><h3 className="font-semibold text-slate-900">Prompt scorecard</h3><span className="text-xs text-slate-400">0–100</span></div><div className="mt-5 space-y-4">{Object.entries(result.scores).map(([key, value]) => <div key={key}><div className="flex justify-between text-xs"><span className="font-medium text-slate-600">{LABELS[key] ?? key}</span><span className="font-semibold text-slate-700">{value}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${value >= 75 ? "bg-emerald-500" : value >= 45 ? "bg-amber-400" : "bg-rose-400"}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div></div>)}</div>
          {result.missing.length > 0 && <div className="mt-6 border-t border-slate-100 pt-5"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Consider adding</p><div className="mt-3 flex flex-wrap gap-2">{result.missing.map(item => <span key={item} className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-800">+ {item}</span>)}</div></div>}
        </section>
        <div className="space-y-4"><section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"><h3 className="font-semibold text-slate-900">Ways to improve</h3><ul className="mt-4 space-y-3">{result.suggestions.map((suggestion, i) => <li key={i} className="flex gap-3 text-sm leading-5 text-slate-600"><span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-[11px] font-semibold text-indigo-700">{i + 1}</span>{suggestion}</li>)}</ul></section>
          <section className="overflow-hidden rounded-3xl border border-indigo-200 bg-white shadow-sm"><div className="flex items-center justify-between bg-indigo-50/70 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">Ready to use</p><h3 className="mt-0.5 font-semibold text-slate-900">Improved prompt</h3></div><span className="rounded-lg bg-white px-2.5 py-1 text-[10px] font-medium text-indigo-600 shadow-sm">Draft</span></div><pre className="whitespace-pre-wrap p-5 text-sm leading-6 text-slate-700">{result.improved_prompt}</pre></section>
        </div>
      </div>
    </section>}
  </div>;
}
