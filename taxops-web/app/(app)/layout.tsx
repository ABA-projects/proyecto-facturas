"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/sidebar";
import Header from "@/components/layout/header";
import { AuthProvider, useAuth } from "@/lib/auth";

function AppShell({ children }: { children: React.ReactNode }) {
  const { token, loadSession, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Al montar, intentar renovar el access token con el refresh cookie
    loadSession().catch(() => {
      router.push("/login");
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-2xl font-black mb-2">
            <span className="text-brand-orange">Tax</span>
            <span className="text-brand-navy dark:text-white">Ops</span>
          </div>
          <p className="text-gray-400 text-sm">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!token) return null;

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AppShell>{children}</AppShell>
    </AuthProvider>
  );
}
