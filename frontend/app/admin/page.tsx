"use client";

import { useEffect, useState } from "react";
import { api, type AdminCommandStats } from "@/lib/api";

const INDIAN_STATES = [
  "Maharashtra", "Karnataka", "Punjab", "Haryana", "Uttar Pradesh",
  "Rajasthan", "Madhya Pradesh", "Andhra Pradesh", "Tamil Nadu", "Gujarat",
];

export default function AdminPage() {
  const [stats, setStats] = useState<AdminCommandStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Alert form state
  const [alertState, setAlertState] = useState("Maharashtra");
  const [alertLevel, setAlertLevel] = useState("danger");
  const [alertTitle, setAlertTitle] = useState("");
  const [alertMessage, setAlertMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<string | null>(null);
  const [alertLoading, setAlertLoading] = useState(false);

  function loadStats() {
    api.adminStats()
      .then(setStats)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadStats();
  }, []);

  async function sendAlert(e: React.FormEvent) {
    e.preventDefault();
    if (!alertTitle.trim() || !alertMessage.trim()) return;
    setAlertLoading(true);
    setAlertStatus(null);

    try {
      await api.broadcastAlert(alertTitle, alertMessage, alertLevel, alertState);
      setAlertStatus(`✓ Emergency alert broadcast queued for ${alertState}`);
      setAlertTitle("");
      setAlertMessage("");
      loadStats();
    } catch (err) {
      setAlertStatus("Failed to send alert: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setAlertLoading(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      {/* Title */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight flex items-center gap-2">
            🏛️ Government National Command Center
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            State-level crop disease surveillance, AI model benchmarks, and emergency alert broadcast.
          </p>
        </div>

        <button
          onClick={loadStats}
          className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 rounded-xl text-xs font-bold transition-all"
        >
          🔄 Refresh Command Center
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-xs mb-6">
          ⚠️ {error}
        </div>
      )}

      {/* National KPI Cards */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass p-5 animate-pulse h-24 bg-white/5" />
          ))}
        </div>
      ) : stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {[
            { label: "Registered Farmers", value: stats.total_farmers.toLocaleString(), icon: "👨‍🌾", color: "text-sky-400" },
            { label: "AI Observations", value: stats.total_reports.toLocaleString(), icon: "📋", color: "text-purple-400" },
            { label: "States Covered", value: stats.states_covered, icon: "🗺️", color: "text-amber-400" },
            { label: "AI Accuracy", value: `${stats.model_accuracy}%`, icon: "🎯", color: "text-emerald-400" },
            { label: "Active Alerts", value: stats.alerts_issued, icon: "🔔", color: "text-red-400" },
          ].map(({ label, value, icon, color }) => (
            <div key={label} className="glass p-5 text-center flex flex-col justify-between">
              <div className="text-3xl mb-1">{icon}</div>
              <p className={`text-2xl font-black ${color} tabular-nums`}>{value}</p>
              <p className="text-slate-400 text-xs mt-1 font-semibold">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Emergency Alert Broadcast Form */}
      <div className="glass p-6 mb-8 border-red-500/30">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-extrabold text-white flex items-center gap-2">
            📢 Emergency Advisory Broadcast System
          </h2>
          <span className="text-[10px] font-bold text-red-400 bg-red-500/10 px-2.5 py-1 rounded-md border border-red-500/20">
            SMS & In-App Broadcast
          </span>
        </div>

        <form onSubmit={sendAlert} className="flex flex-col gap-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Target State</label>
              <select
                value={alertState}
                onChange={(e) => setAlertState(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Threat Level</label>
              <select
                value={alertLevel}
                onChange={(e) => setAlertLevel(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="info">Info Notice</option>
                <option value="warning">Warning Alert</option>
                <option value="danger">Danger Outbreak</option>
                <option value="critical">Critical Emergency</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Alert Headline Title</label>
              <input
                type="text"
                value={alertTitle}
                onChange={(e) => setAlertTitle(e.target.value)}
                placeholder="e.g. High Pink Bollworm Hazard"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1">Broadcasting Message Body</label>
            <textarea
              value={alertMessage}
              onChange={(e) => setAlertMessage(e.target.value)}
              placeholder="e.g. Environmental and AI diagnostic indicators show heightened threat of fungal outbreak across Pune & Nashik. Immediate preventative spray advised."
              className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white h-20 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div className="flex items-center justify-between pt-1">
            <button
              type="submit"
              disabled={alertLoading || !alertTitle.trim() || !alertMessage.trim()}
              className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-extrabold rounded-xl text-xs shadow-lg transition-all disabled:opacity-50"
            >
              {alertLoading ? "Broadcasting..." : "📣 Broadcast Emergency Advisory"}
            </button>

            {alertStatus && (
              <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-lg border border-emerald-500/20">
                {alertStatus}
              </span>
            )}
          </div>
        </form>
      </div>

      {/* Model & Architecture Benchmarks */}
      <div className="glass p-6">
        <h2 className="text-base font-extrabold text-white mb-4 flex items-center gap-2">
          ⚡ KrushiRakshak AI Model Benchmarks
        </h2>
        <div className="grid md:grid-cols-4 gap-4">
          {[
            { label: "EfficientNet-B0 Accuracy", value: "94.2%", trend: "Calibrated T=1.45" },
            { label: "Grad-CAM Heatmap Speed", value: "85 ms", trend: "ResNet / Conv layer hook" },
            { label: "Open-Meteo API Sync", value: "100%", trend: "Live 5-day daily forecast" },
            { label: "PostGIS Spatial Index", value: "GIST (4326)", trend: "5km radius query" },
          ].map(({ label, value, trend }) => (
            <div key={label} className="bg-white/5 rounded-xl border border-white/5 p-4">
              <p className="text-slate-400 text-[11px] font-semibold mb-1 uppercase tracking-wider">{label}</p>
              <p className="text-xl font-extrabold text-white">{value}</p>
              <p className="text-emerald-400 text-[11px] font-medium mt-1">{trend}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
