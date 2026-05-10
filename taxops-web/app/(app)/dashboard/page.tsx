"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, ClipboardList, Bot, Users, TrendingUp, AlertTriangle, CheckCircle, Clock, Calculator, CalendarDays } from "lucide-react";
import { useApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type Stats = {
  total_invoices: number;
  total_exogenas: number;
  total_users: number;
  total_clients: number;
  total_nomina?: number;
  invoices_this_month: number;
  recent_sessions: Array<{
    id: string;
    total_archivos: number;
    nuevas: number;
    errores: number;
    status: string;
    started_at: string;
  }>;
};

export default function DashboardPage() {
  const { get } = useApi();
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === "owner" || user?.role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }
    get<Stats>("/admin/stats")
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, [isAdmin]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Bienvenido{user?.email ? `, ${user.email.split("@")[0]}` : ""}
        </h2>
        <p className="text-gray-500 mt-1">
          Selecciona un módulo para empezar o revisa la actividad reciente.
        </p>
      </div>

      {/* Stats */}
      {isAdmin && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Facturas procesadas"
            value={stats?.total_invoices}
            sub={`${stats?.invoices_this_month ?? 0} este mes`}
            icon={<FileText size={20} className="text-brand-orange" />}
            loading={loading}
          />
          <StatCard
            label="Registros exógenas"
            value={stats?.total_exogenas}
            icon={<ClipboardList size={20} className="text-blue-500" />}
            loading={loading}
          />
          <StatCard
            label="Usuarios activos"
            value={stats?.total_users}
            icon={<Users size={20} className="text-emerald-500" />}
            loading={loading}
          />
          <StatCard
            label="Clientes"
            value={stats?.total_clients}
            icon={<TrendingUp size={20} className="text-violet-500" />}
            loading={loading}
          />
          <StatCard
            label="Cálculos de nómina"
            value={stats?.total_nomina ?? 0}
            icon={<Calculator size={20} className="text-amber-500" />}
            loading={loading}
          />
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <QuickAction
          href="/facturas"
          icon="🧾"
          title="Facturas DIAN"
          description="Procesa PDF/XML. Extrae CUFE, IVA, retención y genera Excel."
          color="orange"
        />
        <QuickAction
          href="/exogenas"
          icon="📋"
          title="Exógenas"
          description="Procesa certificados de retención. Genera Formato 1003 DIAN."
          color="blue"
        />
        <QuickAction
          href="/nomina"
          icon="💼"
          title="Liquidación Nómina"
          description="Calcula nómina mensual, parafiscales y liquidación definitiva CST Colombia."
          color="amber"
        />
        <QuickAction
          href="/calendario"
          icon="📅"
          title="Calendario DIAN"
          description="Fechas tributarias 2026: retención, IVA, renta, exógenas. Exporta a calendario."
          color="cyan"
        />
        <QuickAction
          href="/chatbot"
          icon="🤖"
          title="Chatbot IA"
          description="Consulta normativa DIAN, IVA, retención en la fuente y más."
          color="violet"
        />
        {isAdmin && (
          <QuickAction
            href="/admin/usuarios"
            icon="👥"
            title="Administrar"
            description="Gestiona usuarios, clientes y configuración de la organización."
            color="emerald"
          />
        )}
      </div>

      {/* Recent sessions */}
      {isAdmin && stats && stats.recent_sessions.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Actividad reciente
          </h3>
          <div className="space-y-2">
            {stats.recent_sessions.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
              >
                <div className="flex items-center gap-3">
                  {s.status === "done" ? (
                    <CheckCircle size={16} className="text-emerald-500 shrink-0" />
                  ) : s.status === "failed" ? (
                    <AlertTriangle size={16} className="text-red-500 shrink-0" />
                  ) : (
                    <Clock size={16} className="text-gray-400 shrink-0" />
                  )}
                  <div>
                    <p className="text-sm text-gray-900">
                      {s.total_archivos} archivos — {s.nuevas} nuevas · {s.errores} errores
                    </p>
                    <p className="text-xs text-gray-400">
                      {new Date(s.started_at).toLocaleString("es-CO")}
                    </p>
                  </div>
                </div>
                <span
                  className={`badge text-xs px-2 py-1 ${
                    s.status === "done"
                      ? "bg-emerald-50 text-emerald-700"
                      : s.status === "failed"
                      ? "bg-red-50 text-red-700"
                      : "bg-yellow-50 text-yellow-700"
                  }`}
                >
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  sub,
  icon,
  loading,
}: {
  label: string;
  value?: number;
  sub?: string;
  icon: React.ReactNode;
  loading: boolean;
}) {
  return (
    <div className="card flex items-start gap-4">
      <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
      <div>
        {loading ? (
          <div className="h-6 w-12 bg-gray-200 rounded animate-pulse mb-1" />
        ) : (
          <p className="text-2xl font-bold text-gray-900">
            {value?.toLocaleString("es-CO") ?? "—"}
          </p>
        )}
        <p className="text-sm text-gray-500">{label}</p>
        {sub && <p className="text-xs text-gray-400">{sub}</p>}
      </div>
    </div>
  );
}

function QuickAction({
  href,
  icon,
  title,
  description,
  color,
}: {
  href: string;
  icon: string;
  title: string;
  description: string;
  color: "orange" | "blue" | "violet" | "emerald" | "amber" | "cyan";
}) {
  const borders: Record<string, string> = {
    orange: "border-t-brand-orange",
    blue: "border-t-blue-500",
    violet: "border-t-violet-500",
    emerald: "border-t-emerald-500",
    amber: "border-t-amber-500",
    cyan: "border-t-cyan-500",
  };

  return (
    <Link
      href={href}
      className={`card border-t-4 ${borders[color]} hover:shadow-md transition-all hover:-translate-y-0.5 block`}
    >
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
    </Link>
  );
}
