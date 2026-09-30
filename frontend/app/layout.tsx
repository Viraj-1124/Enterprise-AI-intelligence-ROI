import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";
import { AuthGate, AuthProvider } from "@/components/AuthProvider";

export const metadata: Metadata = {
  title: "Enterprise AI Intelligence & ROI Platform",
  description: "Measuring AI usage, work activity, outcomes, and estimated ROI.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-slate-50 font-sans text-slate-900">
        <AuthProvider><NavBar />
          <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8"><AuthGate>{children}</AuthGate></main>
        </AuthProvider>
      </body>
    </html>
  );
}
