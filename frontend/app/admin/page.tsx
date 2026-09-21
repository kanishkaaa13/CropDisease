"use client";

import { useEffect, useState, useCallback } from "react";
import { api, type AdminSummary, type DistrictAnalytics, type Outbreak, type RiskTrendData } from "@/lib/api";
import OfficerMap from "@/components/OfficerMap";
import AdminHotspotMap from "@/components/AdminHotspotMap";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import GovResourceLinks from "@/components/GovResourceLinks";
import { useTranslations } from "@/lib/i18n";
import SeverityBadge from "@/components/SeverityBadge";

export default function AdminPage() {
  const t = useTranslations();
  const [summary, setSummary] = useState<AdminSummary | null>(null);
  const [districtData, setDistrictData] = useState<DistrictAnalytics[]>([]);
  const [outbreaks, setOutbreaks] = useState<Outbreak[]>([]);
  const [riskTrend, setRiskTrend] = useState<RiskTrendData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Table state
  const [sortBy, setSortBy] = useState("risk_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [filterDistrict, setFilterDistrict] = useState("");
  
  // Map filter state
  const [hotspotFilter, setHotspotFilter] = useState<"all" | "fungal" | "pest">("all");

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
      const [s, d, o, r] = await Promise.all([
        api.adminSummary(),
        api.adminDistrictAnalytics("Maharashtra", sortBy, sortOrder),
        api.adminOutbreaks(30.0),
        api.adminRiskTrend("Maharashtra", 30),
      ]);
      setSummary(s);
      setDistrictData(d);
      setOutbreaks(o);
      setRiskTrend(r);
    } catch (e: any) {
      if (e.name === 'AbortError') {
        setError('Request timed out. Please try again.');
      } else {
        setError(e.message || 'Failed to load data');
      }
    } finally {
      clearTimeout(timeout);
      setLoading(false);
      setRefreshing(false);
    }
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
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            {t("admin.title")}
          </h1>
          <p className="text-slate-400 text-sm mt-2">{t("admin.subtitle")}</p>
        </div>
        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20"
        >
          {refreshing ? 'Refreshing...' : t("admin.refresh")}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-xs mb-6">
          ⚠️ {error}
        </div>
      )}

      <div className="mb-6 max-w-sm">
        <GovResourceLinks compact />
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass p-4 animate-pulse h-28 bg-white/5 rounded-lg border border-white/10" />
          ))}
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            {[
              { 
                label: "Monitored Farms", 
                value: summary?.total_monitored_farms ?? 0, 
                icon: "🏡",
                color: "text-sky-400",
                bgColor: "bg-sky-500/10",
                borderColor: "border-sky-500/20"
              },
              { 
                label: "Active Alerts", 
                value: summary?.active_alerts ?? 0, 
                icon: "🚨",
                color: "text-red-400",
                bgColor: "bg-red-500/10",
                borderColor: "border-red-500/20"
              },
              { 
                label: "High-Risk Villages", 
                value: summary?.high_risk_villages ?? 0, 
                icon: "⚠️",
                color: "text-orange-400",
                bgColor: "bg-orange-500/10",
                borderColor: "border-orange-500/20"
              },
              { 
                label: "Disease Outbreaks", 
                value: summary?.disease_outbreaks_detected ?? 0, 
                icon: "🦠",
                color: "text-amber-400",
                bgColor: "bg-amber-500/10",
                borderColor: "border-amber-500/20"
              },
              { 
                label: "Pending Validations", 
                value: summary?.pending_expert_validations ?? 0, 
                icon: "📋",
                color: "text-purple-400",
                bgColor: "bg-purple-500/10",
                borderColor: "border-purple-500/20"
              },
            ].map(({ label, value, icon, color, bgColor, borderColor }) => (
              <div 
                key={label} 
                className={`glass p-5 rounded-xl border ${borderColor} ${refreshing ? 'opacity-50' : ''} transition-all duration-200 hover:border-white/20`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-3xl">{icon}</span>
                  <SeverityBadge severity={value > 10 ? "HIGH" : value > 5 ? "MODERATE" : "LOW"} />
                </div>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{label}</p>
                <p className={`text-3xl font-bold ${color} tabular-nums mt-2`}>
                  {value}
                </p>
              </div>
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Maharashtra Risk Hotspots Map */}
            <div className="glass p-5 rounded-xl border border-white/10">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-base font-semibold text-white">🗺️ Risk Hotspots Map</h2>
                <div className="flex gap-1">
                  {["all", "fungal", "pest"].map((filter) => (
                    <button
                      key={filter}
                      onClick={() => setHotspotFilter(filter as any)}
                      className={`px-2 py-1 text-[10px] font-semibold rounded transition-colors ${
                        hotspotFilter === filter
                          ? "bg-emerald-500 text-white"
                          : "bg-white/5 text-slate-400 hover:bg-white/10"
                      }`}
                    >
                      {filter === "all" ? "All" : filter === "fungal" ? "Fungal" : "Pest"}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-80 rounded-lg overflow-hidden">
                <AdminHotspotMap filter={hotspotFilter} />
              </div>
            </div>

            {/* Risk Trend Chart */}
            <div className="glass p-5 rounded-xl border border-white/10">
              <h2 className="text-base font-semibold text-white mb-5">📈 Statewide Risk Trend (30 Days)</h2>
              <div className="h-80 rounded-lg overflow-hidden">
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
          <div className="glass p-5 rounded-xl border border-white/10 mb-8">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-semibold text-white">📊 District Analytics</h2>
              <input
                type="text"
                placeholder="Filter district..."
                value={filterDistrict}
                onChange={(e) => setFilterDistrict(e.target.value)}
                className="bg-slate-900/50 border border-white/10 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 transition-all duration-200"
              />
            </div>
            <div className="overflow-x-auto rounded-lg">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10 bg-white/5">
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
                        className="text-left py-3 px-4 text-slate-400 font-semibold cursor-pointer hover:text-white hover:bg-white/5 transition-all duration-200"
                      >
                        {label} {sortBy === key && (sortOrder === "asc" ? "↑" : "↓")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredDistricts.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-12 text-center text-slate-500 text-sm">
                        <div className="flex flex-col items-center gap-3">
                          <span className="text-4xl">📊</span>
                          <span className="text-slate-400">No district data available</span>
                        </div>
                      </td>
                    </tr>
                  ) : filteredDistricts.map((row) => (
                    <tr key={row.district} className="border-b border-white/5 hover:bg-white/5 transition-colors duration-200">
                      <td className="py-3 px-4 text-white font-medium">{row.district}</td>
                      <td className="py-3 px-4 text-slate-300">{row.dominant_crop || 'N/A'}</td>
                      <td className="py-3 px-4 text-slate-300">{row.dominant_threat || 'None'}</td>
                      <td className="py-3 px-4">
                        <span className={`font-semibold ${
                          row.risk_score >= 70 ? "text-red-400" :
                          row.risk_score >= 50 ? "text-orange-400" :
                          row.risk_score >= 30 ? "text-yellow-400" :
                          "text-emerald-400"
                        }`}>
                          {row.risk_score.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300 tabular-nums">{row.case_count}</td>
                      <td className="py-3 px-4 text-slate-300 tabular-nums">{row.farm_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Emerging Outbreaks Panel */}
          <div className="glass p-5 rounded-xl border border-red-500/30">
            <h2 className="text-base font-semibold text-white mb-5 flex items-center gap-2">
              🚨 Emerging Outbreaks
              <span className="text-xs font-normal text-slate-400">Week-over-week growth &gt;30%</span>
            </h2>
            {outbreaks.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm flex flex-col items-center gap-3">
                <span className="text-4xl">✅</span>
                <span>No emerging outbreaks detected</span>
              </div>
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
