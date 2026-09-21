"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useI18n, type Locale } from "@/lib/i18n";
import { useAuth } from "@/lib/auth-context";

const NAV_LINKS = [
  { href: "/farmer", key: "nav.farmer" },
  { href: "/predict", key: "nav.predict" },
  { href: "/officer", key: "nav.officer" },
  { href: "/admin", key: "nav.admin" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { locale, setLocale, t, localeNames } = useI18n();
  const { user, logout } = useAuth();

  // Don't show navbar on login/register pages
  if (pathname === "/login" || pathname === "/register") {
    return null;
  }

  return (
    <nav className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-2xl">🌿</span>
          <span className="font-bold text-white text-lg tracking-tight">
            Krushi<span className="text-emerald-400">Rakshak</span>
            <span className="text-xs font-normal text-slate-400 ml-1">AI</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {user ? (
            <>
              {NAV_LINKS.map(({ href, key }) => (
                <Link
                  key={href}
                  href={href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
                    ${pathname.startsWith(href)
                      ? "bg-emerald-600/30 text-emerald-300 border border-emerald-600/40"
                      : "text-slate-400 hover:text-white hover:bg-white/10"
                    }`}
                >
                  {t(key)}
                </Link>
              ))}
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-white/10">
                <span className="text-sm text-slate-300">{user.full_name}</span>
                <button
                  onClick={logout}
                  className="text-sm text-slate-400 hover:text-white transition-colors"
                >
                  Sign out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/10 transition-all"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
              >
                Register
              </Link>
            </>
          )}
        </div>

        <label className="hidden md:flex items-center gap-2 text-xs text-slate-400">
          <span className="sr-only">{t("nav.language")}</span>
          <span aria-hidden="true">文</span>
          <select
            value={locale}
            onChange={(event) => setLocale(event.target.value as Locale)}
            className="bg-slate-900 text-slate-200 border border-white/10 rounded-lg px-2 py-1.5 outline-none focus:border-emerald-500"
            aria-label={t("nav.language")}
          >
            {(Object.keys(localeNames) as Locale[]).map((code) => (
              <option key={code} value={code}>{localeNames[code]}</option>
            ))}
          </select>
        </label>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-slate-400 hover:text-white"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {open
              ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            }
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden px-4 pb-4 flex flex-col gap-1 border-t border-white/10 mt-1">
          {user ? (
            <>
              {NAV_LINKS.map(({ href, key }) => (
                <Link
                  key={href}
                  href={href}
                  onClick={() => setOpen(false)}
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all
                    ${pathname.startsWith(href)
                      ? "bg-emerald-600/30 text-emerald-300"
                      : "text-slate-400 hover:text-white hover:bg-white/10"
                    }`}
                >
                  {t(key)}
                </Link>
              ))}
              <div className="px-4 py-3 border-t border-white/10 mt-2 pt-4">
                <p className="text-sm text-slate-300 mb-2">{user.full_name}</p>
                <button
                  onClick={() => {
                    logout();
                    setOpen(false);
                  }}
                  className="text-sm text-slate-400 hover:text-white transition-colors"
                >
                  Sign out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                href="/login"
                onClick={() => setOpen(false)}
                className="px-4 py-3 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/10 transition-all"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                onClick={() => setOpen(false)}
                className="px-4 py-3 rounded-lg text-sm font-medium bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
              >
                Register
              </Link>
            </>
          )}
          <label className="flex items-center justify-between px-4 py-3 text-sm text-slate-400 border-t border-white/10 mt-2">
            <span>{t("nav.language")}</span>
            <select
              value={locale}
              onChange={(event) => setLocale(event.target.value as Locale)}
              className="bg-slate-900 text-slate-200 border border-white/10 rounded-lg px-2 py-1.5"
              aria-label={t("nav.language")}
            >
              {(Object.keys(localeNames) as Locale[]).map((code) => (
                <option key={code} value={code}>{localeNames[code]}</option>
              ))}
            </select>
          </label>
        </div>
      )}
    </nav>
  );
}
