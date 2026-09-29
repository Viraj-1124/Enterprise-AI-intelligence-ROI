"use client";

import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export function BarChartCard({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] sm:p-6">
      <div className="flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-slate-800">{title}</h3><span className="rounded-lg bg-indigo-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-600">Overview</span></div>
      {data.length === 0 ? (
        <div className="mt-5 flex h-64 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 text-sm text-slate-400">No data yet</div>
      ) : (
        <div className="mt-3 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} dy={8} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} dx={-4} />
              <Tooltip cursor={{ fill: "#f8fafc" }} contentStyle={{ border: "1px solid #e2e8f0", borderRadius: 12, boxShadow: "0 8px 24px rgba(15,23,42,.08)" }} />
              <Bar dataKey="value" fill="#6366f1" radius={[7, 7, 0, 0]} maxBarSize={46} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export function PieChartCard({ title, data }: { title: string; data: { name: string; value: number }[] }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] sm:p-6">
      <div className="flex items-center justify-between gap-3"><h3 className="text-sm font-semibold text-slate-800">{title}</h3><span className="rounded-lg bg-violet-50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-violet-600">Providers</span></div>
      {data.length === 0 ? (
        <div className="mt-5 flex h-64 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 text-sm text-slate-400">No AI usage recorded yet</div>
      ) : (
        <div className="mt-3 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" outerRadius={88} innerRadius={58} paddingAngle={3} stroke="white" strokeWidth={3}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ border: "1px solid #e2e8f0", borderRadius: 12, boxShadow: "0 8px 24px rgba(15,23,42,.08)" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
