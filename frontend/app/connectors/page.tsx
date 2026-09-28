import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ConnectorsPage() {
  const connectors = await api.connectors().catch(() => []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Connectors</h1>
        <p className="mt-1 text-sm text-gray-500">
          Honest availability status. A connector reports <code>unavailable</code> rather than fabricating data when
          it has no legitimate external source to draw from.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {connectors.map((c) => (
          <div key={c.name} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="font-medium capitalize text-gray-900">{c.name}</h3>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  c.available ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"
                }`}
              >
                {c.available ? "Available" : "Unavailable"}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-500">{c.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
