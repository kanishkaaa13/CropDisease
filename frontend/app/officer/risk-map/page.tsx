"use client";

import OfficerMap from "@/components/OfficerMap";

export default function OfficerRiskMapPage() {
  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-300">Field intelligence</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-100">Maharashtra Risk Hotspots</h1>
        <p className="mt-2 max-w-2xl text-sm text-stone-400">Explore active crop disease observations, district risk, and validation priorities across Maharashtra.</p>
      </header>
      <OfficerMap />
    </div>
  );
}
