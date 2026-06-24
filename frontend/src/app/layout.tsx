import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Learn God Speed",
  description: "Goal-conditioned, hands-on learning for software frameworks",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-semibold tracking-tight text-lg text-accent">
            Learn God Speed
          </Link>
          <nav className="text-sm text-white/60 flex gap-4">
            <Link href="/dashboard" className="hover:text-white">
              Dashboard
            </Link>
          </nav>
        </header>
        <main className="px-6 py-8 max-w-4xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
