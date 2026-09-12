"use client";

import { useEffect, useState } from "react";
import { api, type AdminCommandStats } from "@/lib/api";

export default function AdminPage() {
  const [stats, setStats] = useState<AdminCommandStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Alert form state
  const [alertState, setAlertState] = useState("Maharashtra");
  const [alertMessage, setAlertMessage] = useState("");
  const [alertStatus, setAlertStatus] = useState<string | null>(null);
  const [alertLoading, setAlertLoading] = useState(false);

  useEffect(() => {
    api.adminStats()
      .then(setStats)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function sendAlert(e: React.FormEvent) {
    e.preventDefault();
    setAlertLoading(true);
    try {
      const res = await api.broadcastAlert(alertState, alertMessage);
      setAlertStatus(`✓ Alert queued for ${alertState}`);
      setAlertMessage("");
    } catch {
      setAlertStatus("Failed to send alert.");
    } finally {
      setAlertLoading(false);
    }
  }

  const INDIAN_STATES = [
    "Maharashtra", "Karnataka", "Punjab", "Haryana", "Uttar Pradesh",
    "Rajasthan", "Madhya Pradesh", "Andhra Pradesh", "Tamil Nadu", "Gujarat",
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">🏛️ Government Command Center</h1>
        <p className="text-slate-400">National overview, model performance, and state-wide alert broadcasting.</p>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-xl px-4 py-3 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {/* National KPIs */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="glass p-5 animate-pulse h-24 bg-white/5" />
          ))}
        </div>
      ) : stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {[
            { label: "Total Farmers", value: stats.total_farmers.toLocaleString(), icon: "👨‍🌾" },
            { label: "Total Reports", value: stats.total_reports.toLocaleString(), icon: "📋" },
            { label: "States Covered", value: stats.states_covered, icon: "🗺️" },
            { label: "Model Accuracy", value: `${(stats.model_accuracy * 100).toFixed(1)}%`, icon: "🎯" },
            { label: "Alerts Issued", value: stats.alerts_issued, icon: "🔔" },
          ].map(({ label, value, icon }) => (
            <div key={label} className="glass p-5 text-center">
              <div className="text-3xl mb-2">{icon}</div>
              <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
              <p className="text-slate-500 text-xs mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Alert broadcast form */}
      <div className="glass p-6 mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">📢 Broadcast Advisory Alert</h2>
        <form onSubmit={sendAlert} className="flex flex-col gap-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Target State</label>
              <select
                value={alertState}
                onChange={(e) => setAlertState(e.target.value)}
                className="w-full bg-slate-800/80 border border-white/10 rounded-xl px-4 py-2 text-white text-sm focus:outline-none focus:border-emerald-500"
                id="alert-state-select"
              >
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Alert Message</label>
              <input
                type="text"
                value={alertMessage}
                onChange={(e) => setAlertMessage(e.target.value)}
                placeholder="e.g., High wheat rust risk — apply fungicide"
                className="w-full bg-slate-800/80 border border-white/10 rounded-xl px-4 py-2 text-white text-sm placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                id="alert-message-input"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="submit"
              disabled={alertLoading || !alertMessage.trim()}
              className="btn-primary disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {alertLoading ? "Sending…" : "📣 Send Alert"}
            </button>
            {alertStatus && (
              <span className="text-sm text-emerald-400">{alertStatus}</span>
            )}
          </div>
        </form>
      </div>

      {/* Model metrics placeholder */}
      <div className="glass p-6">
        <h2 className="text-lg font-semibold text-white mb-4">📈 Model Performance</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            { label: "ResNet50 Accuracy", value: "94.0%", trend: "+2.1% this month" },
            { label: "XGBoost Risk Score", value: "89.3%", trend: "+0.8% this month" },
            { label: "Avg. Inference Time", value: "120ms", trend: "-15ms improvement" },
          ].map(({ label, value, trend }) => (
            <div key={label} className="bg-slate-800/40 rounded-xl border border-white/5 p-4">
              <p className="text-slate-400 text-xs mb-1">{label}</p>
              <p className="text-2xl font-bold text-white">{value}</p>
              <p className="text-emerald-400 text-xs mt-1">{trend}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
