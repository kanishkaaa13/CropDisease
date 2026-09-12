import Link from "next/link";
import HealthBadge from "@/components/HealthBadge";

const PORTALS = [
  {
    href: "/farmer",
    emoji: "🌾",
    title: "Farmer App",
    description: "Upload crop photos, get instant disease diagnosis & treatment advisory in your language.",
    color: "from-green-600/30 to-emerald-700/20 border-green-600/30",
    badge: "Mobile First",
  },
  {
    href: "/officer",
    emoji: "📊",
    title: "Officer Dashboard",
    description: "Monitor district-level disease outbreaks, severity heatmaps, and field reports.",
    color: "from-blue-600/30 to-cyan-700/20 border-blue-600/30",
    badge: "District Level",
  },
  {
    href: "/admin",
    emoji: "🏛️",
    title: "Government Command Center",
    description: "National KPI dashboard, model performance metrics, and state-wide alert broadcasting.",
    color: "from-purple-600/30 to-violet-700/20 border-purple-600/30",
    badge: "National",
  },
];

export default function HomePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-16">
      {/* Hero */}
      <div className="text-center mb-16">
        <p className="text-emerald-400 font-semibold tracking-widest text-sm uppercase mb-4">
          Powered by AI · Built for Bharat
        </p>
        <h1 className="text-5xl md:text-6xl font-extrabold text-white leading-tight mb-6">
          KrushiRakshak
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-300">
            AI Platform
          </span>
        </h1>
        <p className="text-slate-400 text-xl max-w-2xl mx-auto mb-8">
          End-to-end AI solution for crop disease detection, real-time weather risk, and
          advisory generation — connecting farmers, officers, and policy-makers.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <HealthBadge />
          <Link href="/farmer" className="btn-primary">
            Start Diagnosing →
          </Link>
        </div>
      </div>

      {/* Portal cards */}
      <div className="grid md:grid-cols-3 gap-6">
        {PORTALS.map(({ href, emoji, title, description, color, badge }) => (
          <Link
            key={href}
            href={href}
            className={`glass p-6 flex flex-col gap-4 bg-gradient-to-br ${color} hover:scale-[1.02] transition-transform duration-200 group`}
          >
            <div className="flex items-start justify-between">
              <span className="text-4xl">{emoji}</span>
              <span className="text-xs font-semibold text-white/50 border border-white/20 px-2 py-0.5 rounded-full">
                {badge}
              </span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white mb-2 group-hover:text-emerald-300 transition-colors">
                {title}
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
            </div>
            <span className="text-emerald-400 text-sm font-semibold mt-auto">
              Open portal →
            </span>
          </Link>
        ))}
      </div>

      {/* Tech stack badges */}
      <div className="mt-16 text-center">
        <p className="text-slate-500 text-xs uppercase tracking-widest mb-4">Tech Stack</p>
        <div className="flex flex-wrap justify-center gap-2">
          {["FastAPI", "PostgreSQL", "PyTorch", "Next.js 14", "Tailwind CSS", "Docker"].map((t) => (
            <span key={t} className="glass px-3 py-1 text-xs text-slate-300">
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
