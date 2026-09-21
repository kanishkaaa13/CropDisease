"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function NotAuthorizedPage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-4xl font-semibold text-neutral-900 mb-2">Not Authorized</h1>
          <p className="text-lg text-neutral-600">
            {user
              ? `You don't have permission to access this page as a ${user.role}.`
              : "You need to sign in to access this page."}
          </p>
        </div>

        <div className="space-y-4">
          {user ? (
            <>
              {user.role === "farmer" && (
                <Link
                  href="/farmer"
                  className="inline-block w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-sm transition-colors"
                >
                  Go to Farmer Dashboard
                </Link>
              )}
              {user.role === "officer" && (
                <Link
                  href="/officer"
                  className="inline-block w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-sm transition-colors"
                >
                  Go to Officer Dashboard
                </Link>
              )}
              {user.role === "admin" && (
                <Link
                  href="/admin"
                  className="inline-block w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-sm transition-colors"
                >
                  Go to Admin Dashboard
                </Link>
              )}
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="inline-block w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg text-sm transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/"
                className="inline-block w-full py-3 border border-neutral-300 text-neutral-700 font-medium rounded-lg text-sm hover:bg-neutral-100 transition-colors"
              >
                Go to Home
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
