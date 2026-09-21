"use client";

import { GOV_RESOURCES } from "@/config/govResources";
import { useTranslations } from "@/lib/i18n";
import { useState } from "react";

interface GovResourceLinksProps {
  compact?: boolean;
}

export default function GovResourceLinks({ compact = false }: GovResourceLinksProps) {
  const t = useTranslations();
  const [selectedCategory, setSelectedCategory] = useState("all");
  const resources = GOV_RESOURCES.filter((resource) => resource.status !== "broken");
  const categories = Array.from(new Set(resources.map((resource) => resource.category)));
  const visibleResources = selectedCategory === "all"
    ? resources
    : resources.filter((resource) => resource.category === selectedCategory);
  const groupedResources = categories.reduce<Record<string, typeof resources>>((groups, category) => {
    const categoryResources = visibleResources.filter((resource) => resource.category === category);
    if (categoryResources.length > 0) groups[category] = categoryResources;
    return groups;
  }, {});

  return (
    <section className={compact ? "glass p-4" : "glass p-5 sm:p-6"} aria-labelledby="government-resources-title">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">{t("resources.eyebrow")}</p>
          <h2 id="government-resources-title" className="mt-1 text-lg font-black text-white">{compact ? t("resources.quick_links") : t("resources.title")}</h2>
        </div>
        <span className="text-xl" aria-hidden="true">🏛️</span>
      </div>
      <div className="mb-4 flex gap-2 overflow-x-auto pb-1" role="group" aria-label={t("resources.filter_label")}>
        {["all", ...categories].map((category) => (
          <button
            key={category}
            type="button"
            onClick={() => setSelectedCategory(category)}
            className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${selectedCategory === category ? "border-emerald-400 bg-emerald-500/20 text-emerald-200" : "border-white/10 text-slate-400 hover:border-emerald-500/40 hover:text-slate-200"}`}
            aria-pressed={selectedCategory === category}
          >
            {category === "all" ? t("resources.all") : t(`resources.categories.${category}`)}
          </button>
        ))}
      </div>
      {resources.length === 0 ? (
        <p className="text-sm text-slate-400">{t("resources.empty")}</p>
      ) : visibleResources.length === 0 ? (
        <p className="text-sm text-slate-400">{t("resources.no_matching")}</p>
      ) : (
        <div className="space-y-5">
          {Object.entries(groupedResources).map(([category, categoryResources]) => (
            <div key={category}>
              <h3 className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{t(`resources.categories.${category}`)}</h3>
              <div className={compact ? "space-y-2" : "grid gap-3 md:grid-cols-2"}>
                {categoryResources.map((resource) => (
                  <article key={resource.id} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 transition hover:border-emerald-500/40 hover:bg-emerald-500/5">
                    <div className="min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-bold leading-5 text-slate-100">{t(resource.nameKey)}</h4>
                        <span className="shrink-0 rounded-full bg-slate-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-300">
                          {t(`resources.scope.${resource.scope}`)}
                        </span>
                      </div>
                      <p className="mt-1 truncate text-xs leading-5 text-slate-400">{t(resource.descriptionKey)}</p>
                      {resource.category === "helpline" && resource.phone && (
                        <a href={`tel:${resource.phone}`} className="mt-1 inline-block text-xs font-semibold text-amber-300 hover:text-amber-200">{resource.phone}</a>
                      )}
                      <a href={resource.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-emerald-300 hover:text-emerald-200">
                        {t("resources.open")} <span aria-hidden="true">↗</span>
                        <span className="font-normal text-slate-500">{t("resources.external")}</span>
                      </a>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
