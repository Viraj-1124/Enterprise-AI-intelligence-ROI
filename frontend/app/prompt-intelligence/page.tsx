"use client";

import { useState } from "react";
import { api, PromptAnalysis } from "@/lib/api";

const LABELS: Record<string, string> = {
  clarity: "Clarity",
  context: "Context",
  specificity: "Specificity",
  output_requirements: "Output requirements",
  ambiguity: "Ambiguity (higher = less ambiguous)",
  completeness: "Completeness",
};

export default function PromptIntelligencePage() {
  const [prompt, setPrompt] = useState("Build an API for users.");
  const [result, setResult] = useState<PromptAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    setLoading(true);
    setError(null);
    try {
      const r = await api.analyzePrompt(prompt);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to analyze prompt");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Prompt Intelligence</h1>
        <p className="mt-1 text-sm text-gray-500">
          Deterministic, rule-based analysis — no LLM call is made here.
        </p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <textarea
          className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-indigo-500 focus:outline-none"
          rows={4}
          placeholder="Enter your prompt..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <button
          onClick={analyze}
          disabled={loading || prompt.trim().length === 0}
          className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Analyze prompt"}
        </button>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {result && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-medium text-gray-700">Scores</h3>
            <div className="mt-3 space-y-3">
              {Object.entries(result.scores).map(([key, val]) => (
                <div key={key}>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{LABELS[key] ?? key}</span>
                    <span>{val}/100</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-gray-100">
                    <div className="h-2 rounded-full bg-indigo-500" style={{ width: `${Math.max(0, Math.min(100, val))}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {result.missing.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs font-medium text-gray-500">Consider adding</h4>
                <ul className="mt-2 space-y-1 text-sm text-gray-700">
                  {result.missing.map((m) => (
                    <li key={m}>✓ {m}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-medium text-gray-700">Suggestions</h3>
              <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-gray-700">
                {result.suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-medium text-gray-700">Improved prompt</h3>
              <pre className="mt-2 whitespace-pre-wrap rounded-lg bg-gray-50 p-3 text-xs text-gray-700">
                {result.improved_prompt}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
