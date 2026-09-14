interface FarmCardProps {
  farmName: string;
  cropName: string;
  healthScore: number;
  riskLevel: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  needsFollowUp: boolean;
  onScan: () => void;
}

export default function FarmCard({ farmName, cropName, healthScore, riskLevel, needsFollowUp, onScan }: FarmCardProps) {
  const riskColors: Record<string, string> = {
    LOW: "bg-emerald-500/20 border-emerald-500/30 text-emerald-400",
    MODERATE: "bg-yellow-500/20 border-yellow-500/30 text-yellow-400",
    HIGH: "bg-orange-500/20 border-orange-500/30 text-orange-400",
    CRITICAL: "bg-red-500/20 border-red-500/30 text-red-400",
  };

  const healthColor = healthScore >= 70 ? "text-emerald-400" : healthScore >= 40 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="glass p-5 rounded-2xl border border-white/10 hover:border-emerald-500/30 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-bold text-white">{farmName}</h3>
          <p className="text-sm text-slate-400">{cropName}</p>
        </div>
        <span className={`px-2 py-1 rounded-lg border text-xs font-bold ${riskColors[riskLevel]}`}>
          {riskLevel}
        </span>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400">Health Score</span>
          <span className={`text-lg font-bold ${healthColor}`}>{healthScore}</span>
        </div>
        <div className="w-full bg-white/10 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${healthScore >= 70 ? "bg-emerald-400" : healthScore >= 40 ? "bg-yellow-400" : "bg-red-400"}`}
            style={{ width: `${healthScore}%` }}
          />
        </div>
      </div>

      {needsFollowUp && (
        <div className="mb-4 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2">
          <p className="text-xs text-amber-300 font-semibold">📋 Follow-up needed</p>
          <p className="text-[10px] text-slate-400">Upload a follow-up photo to check progress</p>
        </div>
      )}

      <button
        onClick={onScan}
        className="w-full py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-sm transition-all flex items-center justify-center gap-2"
      >
        <span>📸</span>
        Scan Crop
      </button>
    </div>
  );
}
