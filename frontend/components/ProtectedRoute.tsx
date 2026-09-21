"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ("farmer" | "officer" | "admin")[];
}

const PUBLIC_PATHS = ["/login", "/register"];

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, loading, setRedirectPath } = useAuth();

  useEffect(() => {
    if (loading) return;

    // Allow public paths
    if (PUBLIC_PATHS.includes(pathname)) {
      return;
    }

    // Redirect to login if not authenticated
    if (!user) {
      setRedirectPath(pathname);
      router.push("/login");
      return;
    }

    // Check role-based access
    if (allowedRoles && !allowedRoles.includes(user.role)) {
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

  // Don't render if not authenticated (redirect in progress)
  if (!user) {
    return null;
  }

  // Don't render if role doesn't match (redirect in progress)
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}
