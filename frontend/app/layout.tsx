import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import { AuthProvider } from "@/lib/auth-context";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "KrushiRakshak AI — Smart Crop Disease Detection",
  description:
    "AI-powered crop disease detection and advisory platform for Indian farmers, district officers, and the government.",
  keywords: ["crop disease", "AI farming", "KrushiRakshak", "agricultural advisory", "India"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <I18nProvider>
            <ProtectedRoute>
              <div className="flex min-h-screen bg-neutral-50">
                <Sidebar />
                <main className="flex-1 lg:ml-0 transition-all duration-300">
                  <div className="max-w-7xl mx-auto px-6 py-8">
                    {children}
                  </div>
                </main>
              </div>
            </ProtectedRoute>
          </I18nProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
