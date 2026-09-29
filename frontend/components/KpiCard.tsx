import ProvenanceBadge from "./ProvenanceBadge";

export default function KpiCard({
  label,
  value,
  source,
  note,
}: {
  label: string;
  value: string;
  source?: string;
  note?: string | null;
}) {
  const accent = source === "observed" || source === "connector" ? "bg-emerald-500" : source === "estimated" ? "bg-violet-500" : "bg-slate-300";
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-900/[0.025] transition duration-200 hover:-translate-y-0.5 hover:shadow-md hover:shadow-slate-900/[0.06]">
      <div className={`absolute inset-x-0 top-0 h-0.5 ${accent}`} />
      <div className="flex min-h-6 items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">{label}</p>
        {source && <ProvenanceBadge source={source} />}
      </div>
      <p className="mt-3 break-words text-[1.7rem] font-semibold tracking-tight text-slate-900">{value}</p>
      {note && <p className="mt-1.5 text-xs leading-5 text-slate-400">{note}</p>}
    </div>
  );
}
