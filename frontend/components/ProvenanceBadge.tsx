const STYLES: Record<string, string> = {
  observed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  connector: "bg-blue-50 text-blue-700 ring-blue-600/20",
  estimated: "bg-amber-50 text-amber-700 ring-amber-600/20",
  imported: "bg-purple-50 text-purple-700 ring-purple-600/20",
  unavailable: "bg-gray-100 text-gray-500 ring-gray-500/20",
};

export default function ProvenanceBadge({ source }: { source: string }) {
  const style = STYLES[source] ?? STYLES.unavailable;
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${style}`}>
      {source.charAt(0).toUpperCase() + source.slice(1)}
    </span>
  );
}
