"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import en from "@/messages/en.json";
import hi from "@/messages/hi.json";
import mr from "@/messages/mr.json";

export type Locale = "en" | "hi" | "mr";
type Messages = typeof en;
type TranslationValues = Record<string, string | number>;

const messages: Record<Locale, Messages> = { en, hi, mr };
const localeNames: Record<Locale, string> = { en: "English", hi: "हिंदी", mr: "मराठी" };

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, values?: TranslationValues) => string;
  localeNames: typeof localeNames;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function routeDefault(pathname: string): Locale {
  return pathname.startsWith("/farmer") ? "mr" : "en";
}

function readValue(source: Messages, key: string): string | undefined {
  const value = key.split(".").reduce<unknown>((current, segment) => {
    if (!current || typeof current !== "object") return undefined;
    return (current as Record<string, unknown>)[segment];
  }, source);
  return typeof value === "string" ? value : undefined;
}

function validLocale(value: string | null): Locale | null {
  return value === "en" || value === "hi" || value === "mr" ? value : null;
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [locale, setLocaleState] = useState<Locale>(() => routeDefault(pathname));

  useEffect(() => {
    const saved = validLocale(window.localStorage.getItem("app_lang"));
    const cookie = validLocale(document.cookie.match(/(?:^|; )app_lang=([^;]+)/)?.[1] ?? null);
    setLocaleState(saved ?? cookie ?? routeDefault(pathname));
  }, [pathname]);

  function setLocale(nextLocale: Locale) {
    setLocaleState(nextLocale);
    window.localStorage.setItem("app_lang", nextLocale);
    document.cookie = `app_lang=${nextLocale}; path=/; max-age=31536000; samesite=lax`;
  }

  function t(key: string, values?: TranslationValues) {
    let result = readValue(messages[locale], key) ?? readValue(messages.en, key) ?? key;
    for (const [name, value] of Object.entries(values ?? {})) {
      result = result.replaceAll(`{${name}}`, String(value));
    }
    return result;
  }

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, localeNames }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}

export function useTranslations() {
  return useI18n().t;
}
