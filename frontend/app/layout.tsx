import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

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
        <Navbar />
        <main className="min-h-screen bg-gradient-to-br from-green-950 via-slate-900 to-emerald-950">
          {children}
        </main>
      </body>
    </html>
  );
}
