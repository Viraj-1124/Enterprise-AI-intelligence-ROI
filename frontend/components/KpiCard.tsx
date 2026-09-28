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
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        {source && <ProvenanceBadge source={source} />}
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-gray-900">{value}</p>
      {note && <p className="mt-1 text-xs text-gray-400">{note}</p>}
    </div>
  );
}
