"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "@/components/Sidebar";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ("farmer" | "officer" | "admin")[];
}

const PUBLIC_PATHS = ["/login", "/register"];
const PROTECTED_PATHS = ["/farmer", "/officer", "/admin", "/predict"];

function dashboardForRole(role: "farmer" | "officer" | "admin") {
  return role === "farmer" ? "/farmer" : "/officer";
}

function roleCanAccessPath(role: "farmer" | "officer" | "admin", pathname: string) {
  if (pathname === "/not-authorized") return true;
  if (pathname === "/admin" || pathname.startsWith("/admin/")) return role === "admin";
  if (pathname === "/officer" || pathname.startsWith("/officer/")) return role === "officer" || role === "admin";
  if (pathname === "/farmer" || pathname.startsWith("/farmer/") || pathname === "/predict" || pathname.startsWith("/predict/")) return role === "farmer";
  return true;
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading, setRedirectPath } = useAuth();

  useEffect(() => {
    if (loading) return;

    // Allow public paths
    if (PUBLIC_PATHS.includes(pathname)) {
      if (user) {
        router.push(dashboardForRole(user.role));
      }
      return;
    }

    if (pathname === "/") {
      router.push(dashboardForRole(user?.role ?? "farmer"));
      return;
    }

    // Redirect to login if not authenticated
    if (!user) {
      if (PROTECTED_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`))) {
        setRedirectPath(pathname);
      }
      router.push("/login");
      return;
    }

    // Check role-based access
    if ((allowedRoles && !allowedRoles.includes(user.role)) || !roleCanAccessPath(user.role, pathname)) {
      router.push("/not-authorized");
      return;
    }
  }, [user, loading, pathname, router, setRedirectPath, allowedRoles]);

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-neutral-600">Loading...</div>
      </div>
    );
  }

  // Don't render protected content on public paths
  if (PUBLIC_PATHS.includes(pathname)) {
    return <>{children}</>;
  }

  if (pathname === "/") {
    return null;
  }

  // Don't render if not authenticated (redirect in progress)
  if (!user) {
    return null;
  }

  // Don't render if role doesn't match (redirect in progress)
  if ((allowedRoles && !allowedRoles.includes(user.role)) || !roleCanAccessPath(user.role, pathname)) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#171b18] text-stone-100">
      <Sidebar />
      <main className="min-h-screen lg:ml-[240px]">
        <div className="mx-auto max-w-7xl px-6 py-6 sm:px-8 sm:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
