"use client";

import { useEffect, useState } from "react";
import { api, type OfficerDashboardStats } from "@/lib/api";

export default function OfficerPage() {
  const [stats, setStats] = useState<OfficerDashboardStats | null>(null);
  const [riskData, setRiskData] = useState<{ district: string; risk_level: string; report_count: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.officerDashboard(), api.riskMap("Maharashtra")])
      .then(([s, r]) => { setStats(s); setRiskData(r); })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const riskColor: Record<string, string> = {
    low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
    high: "text-red-400 bg-red-500/10 border-red-500/20",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-400 text-lg animate-pulse">Loading dashboard…</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">📊 Officer Dashboard</h1>
        <p className="text-slate-400">District-level crop disease monitoring and outbreak tracking.</p>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-sm mb-6">
          {error} — Make sure the backend is running.
        </div>
      )}

      {/* KPI cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Reports", value: stats.total_reports, icon: "📋", color: "text-blue-300" },
            { label: "High Severity", value: stats.high_severity_count, icon: "🔴", color: "text-red-300" },
            { label: "Affected Districts", value: stats.affected_districts, icon: "📍", color: "text-yellow-300" },
            { label: "Top Disease Reports", value: stats.top_diseases[0]?.count ?? 0, icon: "🦠", color: "text-purple-300" },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className="glass p-5">
              <div className="text-2xl mb-2">{icon}</div>
              <p className={`text-3xl font-bold ${color} tabular-nums`}>{value.toLocaleString()}</p>
              <p className="text-slate-400 text-xs mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Risk map placeholder + table */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Map placeholder */}
        <div className="glass p-6 flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white">🗺️ Risk Heatmap</h2>
          <div className="bg-slate-800/50 rounded-xl border border-white/5 h-64 flex items-center justify-center">
            <div className="text-center text-slate-500">
              <div className="text-4xl mb-2">🗺️</div>
              <p className="text-sm">MapLibre GL integration</p>
              <p className="text-xs mt-1">Scaffold ready — wire up map tiles</p>
            </div>
          </div>
        </div>

        {/* District risk table */}
        <div className="glass p-6 flex flex-col gap-4">
          <h2 className="text-lg font-semibold text-white">📍 District Risk Levels</h2>
          {riskData.length === 0 ? (
            <p className="text-slate-500 text-sm">No data yet — submit reports from the Farmer App.</p>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs uppercase tracking-widest border-b border-white/10">
                    <th className="text-left pb-2">District</th>
                    <th className="text-right pb-2">Reports</th>
                    <th className="text-right pb-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {riskData.map((r) => (
                    <tr key={r.district} className="border-b border-white/5">
                      <td className="py-2 text-slate-200">{r.district}</td>
                      <td className="py-2 text-right text-slate-400 tabular-nums">{r.report_count}</td>
                      <td className="py-2 text-right">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${riskColor[r.risk_level] ?? ""}`}>
                          {r.risk_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
