"use client";

import { useEffect, useState } from "react";
import { api, type HealthResponse } from "@/lib/api";

export default function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.health()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs bg-red-500/20 text-red-300 border border-red-500/30 px-3 py-1 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
        Backend unreachable
      </span>
    );
  }

  if (!health) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs bg-slate-700/40 text-slate-400 px-3 py-1 rounded-full animate-pulse">
        Checking…
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full border
      ${health.db_connected
        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
        : "bg-yellow-500/20 text-yellow-300 border-yellow-500/30"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${health.db_connected ? "bg-emerald-400" : "bg-yellow-400"} animate-pulse`} />
      API {health.status} · DB {health.db_connected ? "✓" : "✗"} · v{health.version}
    </span>
  );
}
