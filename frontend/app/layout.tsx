import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n";
import { AuthProvider } from "@/lib/auth-context";
import ProtectedRoute from "@/components/ProtectedRoute";

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
              {children}
            </ProtectedRoute>
          </I18nProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
