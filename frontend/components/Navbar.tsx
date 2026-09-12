"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/farmer",  label: "🌾 Farmer App" },
  { href: "/officer", label: "📊 Officer Dashboard" },
  { href: "/admin",   label: "🏛️ Command Center" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

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
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150
                ${pathname.startsWith(href)
                  ? "bg-emerald-600/30 text-emerald-300 border border-emerald-600/40"
                  : "text-slate-400 hover:text-white hover:bg-white/10"
                }`}
            >
              {label}
            </Link>
          ))}
        </div>

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
          {NAV_LINKS.map(({ href, label }) => (
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
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
