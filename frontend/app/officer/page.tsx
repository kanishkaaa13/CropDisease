"use client";

import { useEffect, useState } from "react";
import {
  api,
  type OfficerDashboardStats,
  type OfficerQueueItem,
} from "@/lib/api";
import OfficerMap from "@/components/OfficerMap";

export default function OfficerPage() {
  const [stats, setStats] = useState<OfficerDashboardStats | null>(null);
  const [queueItems, setQueueItems] = useState<OfficerQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQueueItem, setSelectedQueueItem] = useState<OfficerQueueItem | null>(null);
  const [verdict, setVerdict] = useState<"confirmed" | "corrected" | "referred">("confirmed");
  const [correctedLabel, setCorrectedLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [submittingVal, setSubmittingVal] = useState(false);
  const [userRole, setUserRole] = useState<"officer" | "admin" | null>(null);

  function loadData() {
    setLoading(true);
    Promise.all([
      api.officerDashboard(),
      api.getOfficerQueue(19.0, 73.0, 50),
    ])
      .then(([s, q]) => {
        setStats(s);
        setQueueItems(q);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    // Simple role selector stub
    const role = localStorage.getItem("userRole") as "officer" | "admin" | null;
    setUserRole(role || "officer");
    loadData();
  }, []);

  async function handleValidationSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedQueueItem) return;
    setSubmittingVal(true);

    try {
      await api.submitValidation({
        ai_result_id: selectedQueueItem.ai_result_id,
        officer_id: "officer-1",
        verdict,
        corrected_label: verdict === "corrected" ? correctedLabel : undefined,
        notes,
      });
      setSelectedQueueItem(null);
      setCorrectedLabel("");
      setNotes("");
      loadData();
    } catch (err) {
      alert("Validation failed: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setSubmittingVal(false);
    }
  }

  const riskBadgeClass: Record<string, string> = {
    LOW: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    MODERATE: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    HIGH: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    CRITICAL: "text-red-400 bg-red-500/10 border-red-500/30",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-400 text-sm animate-pulse flex items-center gap-2">
          <svg className="animate-spin w-5 h-5 text-emerald-400" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          Loading District Agronomic Dashboard...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      {/* Title & Role Selector */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">
            📊 Field Officer Command Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Geospatial risk hotspots, prioritized validation queue, and expert review workflow.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={userRole || "officer"}
            onChange={(e) => {
              setUserRole(e.target.value as "officer" | "admin");
              localStorage.setItem("userRole", e.target.value);
            }}
            className="px-3 py-2 bg-white/5 border border-white/10 text-slate-300 rounded-xl text-xs font-bold"
          >
            <option value="officer">Officer</option>
            <option value="admin">Admin</option>
          </select>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-xl text-xs font-bold transition-all"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-xs mb-6">
          ⚠️ {error} — Ensure FastAPI backend is running on port 8000.
        </div>
      )}

      {/* KPI Overview Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Observations", value: stats.total_reports, icon: "📋", color: "text-sky-400" },
            { label: "Severe Outbreaks", value: stats.high_severity_count, icon: "🚨", color: "text-red-400" },
            { label: "Districts Monitored", value: stats.affected_districts, icon: "📍", color: "text-amber-400" },
            { label: "Top Outbreak Class", value: stats.top_diseases[0]?.name || "N/A", icon: "🦠", color: "text-emerald-400" },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className="glass p-5 flex flex-col justify-between">
              <div className="flex items-center justify-between text-2xl mb-2">
                <span>{icon}</span>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Live</span>
              </div>
              <p className={`text-2xl font-extrabold ${color} truncate tabular-nums`}>{value}</p>
              <p className="text-slate-400 text-xs mt-1 font-medium">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Geospatial Risk Hotspots Map */}
      <div className="glass p-6 mb-8">
        <h2 className="text-lg font-black text-white mb-4 flex items-center gap-2">
          🗺️ Maharashtra Risk Hotspots Map
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Color-coded markers show farm clusters by risk level. Click markers for cluster details.
        </p>
        <OfficerMap officerLat={19.0} officerLng={73.0} />
      </div>

      {/* Prioritized Validation Queue */}
      <div className="glass p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-black text-white flex items-center gap-2">
              🔬 Prioritized Validation Queue
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Cases sorted by priority score (risk level, confidence, distance)
            </p>
          </div>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
            {queueItems.length} Cases Pending
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="pb-2">Priority</th>
                <th className="pb-2">Farm & Location</th>
                <th className="pb-2">AI Diagnosis</th>
                <th className="pb-2 text-right">Confidence</th>
                <th className="pb-2 text-right">Risk</th>
                <th className="pb-2 text-right">Distance</th>
                <th className="pb-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {queueItems.slice(0, 10).map((item) => (
                <tr key={item.ai_result_id} className="hover:bg-white/[0.02]">
                  <td className="py-3">
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                      {item.priority_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-3">
                    <p className="font-bold text-slate-200">{item.farm_name}</p>
                    <p className="text-[10px] text-slate-400">{item.district} • {item.taluka}</p>
                  </td>
                  <td className="py-3">
                    <span className="font-semibold text-emerald-300">
                      {item.disease_label ? item.disease_label.replace("___", " - ") : "Scanning..."}
                    </span>
                  </td>
                  <td className="py-3 text-right font-mono font-bold text-slate-300">
                    {item.confidence.toFixed(1)}%
                  </td>
                  <td className="py-3 text-right">
                    <span className={`px-2 py-0.5 rounded-full border font-bold text-[10px] ${riskBadgeClass[item.risk_level] || ""}`}>
                      {item.risk_level}
                    </span>
                  </td>
                  <td className="py-3 text-right font-mono text-slate-400">
                    {item.distance_km.toFixed(1)} km
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setSelectedQueueItem(item)}
                      className="px-3 py-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-xs transition-all shadow"
                    >
                      Validate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Validation Modal */}
      {selectedQueueItem && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass max-w-lg w-full p-6 border-emerald-500/40 shadow-2xl">
            <div className="flex items-center justify-between mb-4 border-b border-white/10 pb-3">
              <h3 className="text-base font-extrabold text-white">
                🔬 Expert Validation: {selectedQueueItem.farm_name}
              </h3>
              <button
                onClick={() => setSelectedQueueItem(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleValidationSubmit} className="flex flex-col gap-4">
              <div className="bg-white/5 p-3 rounded-xl text-xs space-y-1">
                <p><span className="text-slate-400">AI Prediction:</span> <strong className="text-emerald-400">{selectedQueueItem.disease_label}</strong></p>
                <p><span className="text-slate-400">AI Confidence:</span> <strong>{selectedQueueItem.confidence.toFixed(1)}%</strong></p>
                <p><span className="text-slate-400">Risk Level:</span> <strong>{selectedQueueItem.risk_level}</strong></p>
                <p><span className="text-slate-400">Priority Score:</span> <strong>{selectedQueueItem.priority_score.toFixed(1)}</strong></p>
                <p><span className="text-slate-400">Distance:</span> <strong>{selectedQueueItem.distance_km.toFixed(1)} km</strong></p>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-2">Verdict</label>
                <div className="grid grid-cols-3 gap-2">
                  {(["confirmed", "corrected", "referred"] as const).map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => setVerdict(v)}
                      className={`py-2 rounded-xl text-xs font-bold capitalize transition-all border ${
                        verdict === v
                          ? "bg-emerald-500 text-slate-950 border-emerald-400 shadow"
                          : "bg-white/5 text-slate-400 border-white/10 hover:text-white"
                      }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              {verdict === "corrected" && (
                <div>
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Corrected Diagnosis Label</label>
                  <input
                    type="text"
                    value={correctedLabel}
                    onChange={(e) => setCorrectedLabel(e.target.value)}
                    placeholder="e.g. Severe Tomato Late Blight"
                    className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>
              )}

              <div>
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Field Notes / Remarks</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Microscopic field sample confirmed pathogen spore structure."
                  className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white h-20 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedQueueItem(null)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-slate-400 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingVal}
                  className="px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold rounded-xl text-xs shadow-lg transition-all"
                >
                  {submittingVal ? "Submitting..." : "Submit Verdict"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
