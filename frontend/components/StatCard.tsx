interface StatCardProps {
  icon: string;
  label: string;
  value: string | number;
  subtext?: string;
  colorClass?: string;
}

export default function StatCard({ icon, label, value, subtext, colorClass = "text-white" }: StatCardProps) {
  return (
    <div className="glass p-5 flex flex-col gap-2">
      <span className="text-2xl">{icon}</span>
      <p className={`text-3xl font-bold tabular-nums ${colorClass}`}>{value}</p>
      <div>
        <p className="text-slate-300 text-sm font-medium">{label}</p>
        {subtext && <p className="text-slate-500 text-xs mt-0.5">{subtext}</p>}
      </div>
    </div>
  );
}
