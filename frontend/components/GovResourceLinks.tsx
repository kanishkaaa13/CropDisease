"use client";

import { GOV_RESOURCES } from "@/config/govResources";
import { useTranslations } from "@/lib/i18n";

interface GovResourceLinksProps {
  compact?: boolean;
}

export default function GovResourceLinks({ compact = false }: GovResourceLinksProps) {
  const t = useTranslations();

  return (
    <section className={compact ? "glass p-4" : "glass p-5 sm:p-6"} aria-labelledby="government-resources-title">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">{t("resources.eyebrow")}</p>
          <h2 id="government-resources-title" className="mt-1 text-lg font-black text-white">{compact ? t("resources.quick_links") : t("resources.title")}</h2>
        </div>
        <span className="text-xl" aria-hidden="true">🏛️</span>
      </div>
      <div className={compact ? "space-y-2" : "grid gap-3 md:grid-cols-2"}>
        {GOV_RESOURCES.map((resource) => (
          <article key={resource.url} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 transition hover:border-emerald-500/40 hover:bg-emerald-500/5">
            <div className="flex items-start gap-3">
              <span className="text-xl" aria-hidden="true">{resource.icon}</span>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-bold leading-5 text-slate-100">{resource.title}</h3>
                {!compact && <p className="mt-1 text-xs leading-5 text-slate-400">{resource.description}</p>}
                <a href={resource.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-emerald-300 hover:text-emerald-200">
                  {t("resources.open")} <span aria-hidden="true">↗</span>
                  <span className="font-normal text-slate-500">{t("resources.external")}</span>
                </a>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
