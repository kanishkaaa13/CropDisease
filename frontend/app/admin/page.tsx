"use client";

import { useEffect, useState, useCallback } from "react";
import { api, type AdminSummary, type DistrictAnalytics, type Outbreak, type RiskTrendData } from "@/lib/api";
import OfficerMap from "@/components/OfficerMap";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function AdminPage() {
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [districtData, setDistrictData] = useState<DistrictAnalytics[]>([]);
  const [outbreaks, setOutbreaks] = useState<Outbreak[]>([]);
  const [riskTrend, setRiskTrend] = useState<RiskTrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Table state
  const [sortBy, setSortBy] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [filterDistrict, setFilterDistrict] = useState("");

  const loadData = useCallback(() => {
    setLoading(true);
    setError(null);

    Promise.all([
      api.adminSummary(),
      api.adminDistrictAnalytics("Maharashtra", sortBy, sortOrder),
      api.adminOutbreaks(30.0),
      api.adminRiskTrend("Maharashtra", 30),
    ])
      .then(([s, d, o, r]) => {
        setSummary(s);
        setDistrictData(d);
        setOutbreaks(o);
        setRiskTrend(r);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sortBy, sortOrder]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function handleSort(column: string) {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
  }

  const filteredDistricts = districtData.filter(d =>
    !filterDistrict || d.district.toLowerCase().includes(filterDistrict.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🏛️ Government Command Center
          </h1>
          <p className="text-slate-400 text-sm mt-1">Maharashtra State Disease Surveillance Dashboard</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-lg text-xs font-semibold transition-all"
        >
          🔄 Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-xs mb-6">
          ⚠️ {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-5 gap-4 mb-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass p-4 animate-pulse h-24 bg-white/5" />
          ))}
        </div>
      ) : summary && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[
              { label: "Monitored Farms", value: summary.total_monitored_farms, color: "text-sky-400" },
              { label: "Active Alerts", value: summary.active_alerts, color: "text-red-400" },
              { label: "High-Risk Villages", value: summary.high_risk_villages, color: "text-orange-400" },
              { label: "Disease Outbreaks", value: summary.disease_outbreaks_detected, color: "text-amber-400" },
              { label: "Pending Validations", value: summary.pending_expert_validations, color: "text-purple-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="glass p-4 rounded-lg border border-white/10">
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{label}</p>
                <p className={`text-2xl font-bold ${color} tabular-nums`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Maharashtra Map */}
            <div className="glass p-4 rounded-lg border border-white/10">
              <h2 className="text-sm font-bold text-white mb-4">🗺️ Risk Hotspots Map</h2>
              <div className="h-80">
                <OfficerMap officerLat={19.0} officerLng={75.0} />
              </div>
            </div>

            {/* Risk Trend Chart */}
            <div className="glass p-4 rounded-lg border border-white/10">
              <h2 className="text-sm font-bold text-white mb-4">📈 Statewide Risk Trend (30 Days)</h2>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={riskTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#94a3b8"
                      tick={{ fontSize: 10 }}
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    />
                    <YAxis 
                      stroke="#94a3b8"
                      tick={{ fontSize: 10 }}
                      domain={[0, 100]}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                      itemStyle={{ color: '#fff' }}
                      labelStyle={{ color: '#94a3b8' }}
                      formatter={(value: unknown) => [typeof value === 'number' ? value.toFixed(1) : String(value || ''), 'Risk Score']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="avg_risk_score" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      dot={{ fill: '#10b981', r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* District Analytics Table */}
          <div className="glass p-4 rounded-lg border border-white/10 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-bold text-white">📊 District Analytics</h2>
              <input
                type="text"
                placeholder="Filter district..."
                value={filterDistrict}
                onChange={(e) => setFilterDistrict(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    {[
                      { key: "district", label: "District" },
                      { key: "dominant_crop", label: "Dominant Crop" },
                      { key: "dominant_threat", label: "Dominant Threat" },
                      { key: "risk_score", label: "Risk Score" },
                      { key: "case_count", label: "Cases" },
                      { key: "farm_count", label: "Farms" },
                    ].map(({ key, label }) => (
                      <th
                        key={key}
                        onClick={() => handleSort(key)}
                        className="text-left py-2 px-3 text-slate-400 font-semibold cursor-pointer hover:text-white transition-colors"
                      >
                        {label} {sortBy === key && (sortOrder === "asc" ? "↑" : "↓")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredDistricts.map((row) => (
                    <tr key={row.district} className="border-b border-white/5 hover:bg-white/5">
                      <td className="py-2 px-3 text-white font-medium">{row.district}</td>
                      <td className="py-2 px-3 text-slate-300">{row.dominant_crop}</td>
                      <td className="py-2 px-3 text-slate-300">{row.dominant_threat}</td>
                      <td className="py-2 px-3">
                        <span className={`font-bold ${
                          row.risk_score >= 70 ? "text-red-400" :
                          row.risk_score >= 50 ? "text-orange-400" :
                          row.risk_score >= 30 ? "text-yellow-400" :
                          "text-emerald-400"
                        }`}>
                          {row.risk_score.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-slate-300 tabular-nums">{row.case_count}</td>
                      <td className="py-2 px-3 text-slate-300 tabular-nums">{row.farm_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Emerging Outbreaks Panel */}
          <div className="glass p-4 rounded-lg border border-red-500/30">
            <h2 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              🚨 Emerging Outbreaks
              <span className="text-[10px] font-normal text-slate-400">Week-over-week growth &gt;30%</span>
            </h2>
            {outbreaks.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">No emerging outbreaks detected</div>
            ) : (
              <div className="space-y-2">
                {outbreaks.map((o) => (
                  <div key={`${o.village}-${o.disease}`} className="bg-white/5 rounded-lg p-3 border border-white/10">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-white font-semibold text-xs">{o.village}, {o.taluka}</p>
                        <p className="text-slate-400 text-[10px]">{o.district} • {o.crop}</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          o.risk_level === "CRITICAL" ? "bg-red-500/20 text-red-400" :
                          o.risk_level === "HIGH" ? "bg-orange-500/20 text-orange-400" :
                          "bg-yellow-500/20 text-yellow-400"
                        }`}>
                          {o.risk_level}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span>{o.disease}</span>
                      <span className="text-emerald-400 font-bold">+{o.growth_pct}% growth</span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-[10px] text-slate-500">
                      <span>Previous: {o.previous_week_cases} cases</span>
                      <span>Current: {o.current_week_cases} cases</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
