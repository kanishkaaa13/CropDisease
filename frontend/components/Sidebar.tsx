"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight, Leaf, LogOut, Menu, X } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { getNavItems } from "@/lib/navigation";

function getInitials(name: string) {
  return name.trim().split(/\s+/).map((part) => part[0]).join("").toUpperCase().slice(0, 2);
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("sidebar_collapsed");
    if (saved !== null) setCollapsed(saved === "true");
  }, []);

  useEffect(() => {
    localStorage.setItem("sidebar_collapsed", String(collapsed));
  }, [collapsed]);

  useEffect(() => setMobileOpen(false), [pathname]);

  if (!user) return null;

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <button
        type="button"
        aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={mobileOpen}
        className="fixed left-4 top-4 z-50 rounded-lg border border-stone-700 bg-[#202721] p-2 text-stone-200 shadow-lg focus:outline-none focus:ring-2 focus:ring-emerald-400 lg:hidden"
        onClick={() => setMobileOpen((open) => !open)}
      >
        {mobileOpen ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
      </button>

      <aside
        aria-label="Authenticated navigation"
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-stone-700/80 bg-[#202721] text-stone-100 shadow-2xl transition-all duration-200 lg:translate-x-0 ${collapsed ? "lg:w-[72px]" : "lg:w-[240px]"} ${mobileOpen ? "w-[280px] translate-x-0" : "w-[280px] -translate-x-full"}`}
      >
        <div className="flex h-20 items-center border-b border-stone-700/80 px-4">
          <Link href={user.role === "farmer" ? "/farmer" : "/officer"} className="flex min-w-0 items-center gap-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-400">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-700 text-emerald-50">
              <Leaf className="h-5 w-5" aria-hidden="true" />
            </span>
            {!collapsed && <span className="truncate text-base font-semibold tracking-tight">Krushi<span className="text-emerald-400">Rakshak</span></span>}
          </Link>
          <button type="button" aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} className="ml-auto hidden rounded-md p-1.5 text-stone-400 hover:bg-stone-700/60 hover:text-white focus:outline-none focus:ring-2 focus:ring-emerald-400 lg:block" onClick={() => setCollapsed((value) => !value)}>
            {collapsed ? <ChevronRight className="h-4 w-4" aria-hidden="true" /> : <ChevronLeft className="h-4 w-4" aria-hidden="true" />}
          </button>
          <button type="button" aria-label="Close navigation" className="ml-auto rounded-md p-1.5 text-stone-400 hover:bg-stone-700/60 hover:text-white focus:outline-none focus:ring-2 focus:ring-emerald-400 lg:hidden" onClick={() => setMobileOpen(false)}>
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-5" aria-label="Primary">
          <ul className="space-y-1.5">
            {getNavItems(user.role).map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    title={collapsed ? item.label : undefined}
                    aria-current={active ? "page" : undefined}
                    className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-400 ${collapsed ? "justify-center" : ""} ${active ? "bg-emerald-900/45 text-emerald-200" : "text-stone-400 hover:bg-stone-700/50 hover:text-stone-100"}`}
                    onClick={() => setMobileOpen(false)}
                  >
                    {active && <span className="absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r bg-emerald-400" aria-hidden="true" />}
                    <Icon className={`h-5 w-5 shrink-0 ${active ? "text-emerald-300" : "text-stone-500"}`} aria-hidden="true" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-stone-700/80 p-4">
          <div className={`flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-700 text-sm font-semibold text-emerald-50" aria-hidden="true">
              {getInitials(user.full_name)}
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-stone-100">{user.full_name}</p>
                <p className="truncate text-xs capitalize text-stone-500">{user.role}</p>
              </div>
            )}
          </div>
          <button type="button" title={collapsed ? "Sign out" : undefined} aria-label="Sign out" onClick={logout} className={`mt-4 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-stone-400 transition-colors hover:bg-stone-700/50 hover:text-stone-100 focus:outline-none focus:ring-2 focus:ring-emerald-400 ${collapsed ? "justify-center" : ""}`}>
            <LogOut className="h-4 w-4 shrink-0" aria-hidden="true" />
            {!collapsed && <span>Sign out</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
