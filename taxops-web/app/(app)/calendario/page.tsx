"use client";

import { useState, useEffect } from "react";
import { Bell, Calendar, Download, AlertTriangle, CheckCircle, Clock, Filter, ExternalLink } from "lucide-react";
import { PageChatbot } from "@/components/PageChatbot";

/* ── Tipos ─────────────────────────────────────────────────────────────────── */
type TipoEvento = "retencion" | "iva" | "renta" | "exogenas" | "ica" | "patrimonio" | "otro";
type UrgenciaEvento = "critica" | "alta" | "media" | "baja";

type EventoDIAN = {
  id: string;
  fecha: string; // YYYY-MM-DD
  titulo: string;
  descripcion: string;
  tipo: TipoEvento;
  urgencia: UrgenciaEvento;
  articulo?: string;
  link?: string;
  alertaDias?: number; // días antes para alertar
};

/* ── Calendario DIAN 2026 ──────────────────────────────────────────────────── */
const EVENTOS: EventoDIAN[] = [
  // MAYO 2026
  { id: "e1", fecha: "2026-05-19", titulo: "Retención en la fuente — abril", descripcion: "Declaración y pago retención en la fuente mes de abril 2026. Fecha límite NIT terminado en 0.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },
  { id: "e2", fecha: "2026-05-26", titulo: "Declaración renta PYMES", descripcion: "Declaración de renta año gravable 2025 para personas jurídicas no grandes contribuyentes.", tipo: "renta", urgencia: "critica", articulo: "Art. 240 ET", alertaDias: 10 },

  // JUNIO 2026
  { id: "e3", fecha: "2026-06-16", titulo: "IVA bimestral — mar-abr 2026", descripcion: "Declaración y pago IVA bimestre marzo-abril 2026 para responsables del régimen ordinario.", tipo: "iva", urgencia: "alta", articulo: "Art. 600 ET", alertaDias: 5 },
  { id: "e4", fecha: "2026-06-19", titulo: "Retención en la fuente — mayo", descripcion: "Declaración y pago retención en la fuente mes de mayo 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },
  { id: "e5", fecha: "2026-06-30", titulo: "Exógenas 2025 — vencimiento", descripcion: "Último día para presentar información exógena año gravable 2025 (Formato 1003, 1005, 1006, 1007, 1008). Aplica a quienes superaron el tope de ingresos.", tipo: "exogenas", urgencia: "critica", articulo: "Res. DIAN 000162/2023", alertaDias: 15 },

  // JULIO 2026
  { id: "e6", fecha: "2026-07-20", titulo: "Retención en la fuente — junio", descripcion: "Declaración y pago retención en la fuente mes de junio 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },

  // AGOSTO 2026
  { id: "e7", fecha: "2026-08-18", titulo: "IVA bimestral — may-jun 2026", descripcion: "Declaración y pago IVA bimestre mayo-junio 2026.", tipo: "iva", urgencia: "alta", articulo: "Art. 600 ET", alertaDias: 5 },
  { id: "e8", fecha: "2026-08-20", titulo: "Retención en la fuente — julio", descripcion: "Declaración y pago retención en la fuente mes de julio 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },
  { id: "e9", fecha: "2026-08-25", titulo: "Renta personas naturales — inicio", descripcion: "Inicio vencimientos declaración de renta personas naturales y asimiladas año gravable 2025 (grandes patrimonios).", tipo: "renta", urgencia: "alta", articulo: "Art. 592 ET", alertaDias: 10 },

  // SEPTIEMBRE 2026
  { id: "e10", fecha: "2026-09-18", titulo: "Retención en la fuente — agosto", descripcion: "Declaración y pago retención en la fuente mes de agosto 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },

  // OCTUBRE 2026
  { id: "e11", fecha: "2026-10-15", titulo: "IVA bimestral — jul-ago 2026", descripcion: "Declaración y pago IVA bimestre julio-agosto 2026.", tipo: "iva", urgencia: "alta", articulo: "Art. 600 ET", alertaDias: 5 },
  { id: "e12", fecha: "2026-10-20", titulo: "Retención en la fuente — septiembre", descripcion: "Declaración y pago retención en la fuente mes de septiembre 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },
  { id: "e13", fecha: "2026-10-22", titulo: "Renta personas naturales — cierre", descripcion: "Último día vencimiento declaración de renta personas naturales año gravable 2025.", tipo: "renta", urgencia: "critica", articulo: "Art. 592 ET", alertaDias: 15 },

  // NOVIEMBRE 2026
  { id: "e14", fecha: "2026-11-20", titulo: "Retención en la fuente — octubre", descripcion: "Declaración y pago retención en la fuente mes de octubre 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },

  // DICIEMBRE 2026
  { id: "e15", fecha: "2026-12-15", titulo: "IVA bimestral — sep-oct 2026", descripcion: "Declaración y pago IVA bimestre septiembre-octubre 2026.", tipo: "iva", urgencia: "alta", articulo: "Art. 600 ET", alertaDias: 5 },
  { id: "e16", fecha: "2026-12-18", titulo: "Retención en la fuente — noviembre", descripcion: "Declaración y pago retención en la fuente mes de noviembre 2026.", tipo: "retencion", urgencia: "alta", articulo: "Art. 375 ET", alertaDias: 5 },
  { id: "e17", fecha: "2026-12-31", titulo: "Cierre fiscal 2026", descripcion: "Cierre del año gravable 2026. Verificar provisiones, ajustes de inventario, diferencias en cambio y conciliaciones bancarias.", tipo: "otro", urgencia: "critica", alertaDias: 30 },
];

/* ── Estilos por tipo ──────────────────────────────────────────────────────── */
const TIPO_CONFIG: Record<TipoEvento, { label: string; bg: string; text: string; dot: string }> = {
  retencion: { label: "Retención",  bg: "bg-orange-50",  text: "text-orange-700",  dot: "bg-orange-500"  },
  iva:       { label: "IVA",        bg: "bg-blue-50",    text: "text-blue-700",    dot: "bg-blue-500"    },
  renta:     { label: "Renta",      bg: "bg-red-50",     text: "text-red-700",     dot: "bg-red-500"     },
  exogenas:  { label: "Exógenas",   bg: "bg-violet-50",  text: "text-violet-700",  dot: "bg-violet-500"  },
  ica:       { label: "ICA",        bg: "bg-cyan-50",    text: "text-cyan-700",    dot: "bg-cyan-500"    },
  patrimonio:{ label: "Patrimonio", bg: "bg-amber-50",   text: "text-amber-700",   dot: "bg-amber-500"   },
  otro:      { label: "Otro",       bg: "bg-gray-100",   text: "text-gray-700",    dot: "bg-gray-500"    },
};

const URGENCIA_CONFIG: Record<UrgenciaEvento, { label: string; icon: React.ReactNode }> = {
  critica: { label: "Crítica",  icon: <AlertTriangle size={13} className="text-red-500" /> },
  alta:    { label: "Alta",     icon: <Clock size={13} className="text-orange-500" /> },
  media:   { label: "Media",    icon: <Clock size={13} className="text-yellow-500" /> },
  baja:    { label: "Baja",     icon: <CheckCircle size={13} className="text-emerald-500" /> },
};

const MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

function diasRestantes(fecha: string): number {
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const target = new Date(fecha + "T00:00:00");
  return Math.ceil((target.getTime() - hoy.getTime()) / 86400000);
}

const DIAN_SYSTEM = `Eres TaxOps Asistente del Calendario DIAN Colombia 2026. Puedes ayudar con:
- Explicar qué es cada obligación tributaria (retención, IVA, renta, exógenas, ICA)
- Qué artículos del ET regulan cada obligación
- Quiénes están obligados a declarar y pagar
- Cómo calcular los valores a declarar
- Consecuencias de no declarar o no pagar a tiempo (sanciones Art. 641, 642, 644 ET)
- Diferencias entre grandes contribuyentes, PYMES y personas naturales
- Régimen simple de tributación (SIMPLE) vs régimen ordinario
- IVA: bimestral vs cuatrimestral según ingresos
- Información exógena: quién debe reportar, formatos DIAN 1001-1014
Responde en español con referencias al ET colombiano cuando sea relevante.`;

/* ══════════════════════════════════════════════════════════════════════════════ */
export default function CalendarioPage() {
  const [filtroTipo, setFiltroTipo] = useState<TipoEvento | "todos">("todos");
  const [soloProximos, setSoloProximos] = useState(true);
  const [eventoAbierto, setEventoAbierto] = useState<string | null>(null);
  const hoy = new Date().toISOString().slice(0, 10);

  const eventosFiltrados = EVENTOS
    .filter((e) => filtroTipo === "todos" || e.tipo === filtroTipo)
    .filter((e) => !soloProximos || e.fecha >= hoy)
    .sort((a, b) => a.fecha.localeCompare(b.fecha));

  // Agrupar por mes
  const porMes: Record<string, EventoDIAN[]> = {};
  for (const e of eventosFiltrados) {
    const mesKey = e.fecha.slice(0, 7); // YYYY-MM
    if (!porMes[mesKey]) porMes[mesKey] = [];
    porMes[mesKey].push(e);
  }

  // Alertas próximas (≤ 10 días)
  const alertas = EVENTOS.filter((e) => {
    const d = diasRestantes(e.fecha);
    return d >= 0 && d <= 10;
  });

  function exportICS() {
    const lines = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//TaxOps//Calendario DIAN 2026//ES",
      "X-WR-CALNAME:Calendario DIAN 2026",
      "X-WR-TIMEZONE:America/Bogota",
    ];
    for (const e of EVENTOS) {
      const dt = e.fecha.replace(/-/g, "");
      lines.push(
        "BEGIN:VEVENT",
        `DTSTART;VALUE=DATE:${dt}`,
        `DTEND;VALUE=DATE:${dt}`,
        `SUMMARY:📋 ${e.titulo}`,
        `DESCRIPTION:${e.descripcion.replace(/\n/g, "\\n")} ${e.articulo ? "· " + e.articulo : ""}`,
        `CATEGORIES:DIAN,${e.tipo.toUpperCase()}`,
        "END:VEVENT",
      );
    }
    lines.push("END:VCALENDAR");
    const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "taxops-calendario-dian-2026.ics"; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Calendario DIAN 2026</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1 text-sm">
            Fechas tributarias clave · Retención · IVA · Renta · Exógenas
          </p>
        </div>
        <button
          onClick={exportICS}
          className="flex items-center gap-2 text-sm font-semibold bg-brand-navy text-white px-4 py-2 rounded-xl hover:bg-brand-navy/80 transition-colors"
        >
          <Download size={15} />
          Exportar a Calendario (.ics)
        </button>
      </div>

      {/* Alertas próximas */}
      {alertas.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Bell size={16} className="text-red-600" />
            <span className="font-semibold text-red-700 dark:text-red-400 text-sm">
              {alertas.length} obligación{alertas.length > 1 ? "es" : ""} en los próximos 10 días
            </span>
          </div>
          <div className="space-y-2">
            {alertas.map((e) => {
              const d = diasRestantes(e.fecha);
              return (
                <div key={e.id} className="flex items-center justify-between text-sm">
                  <span className="text-red-700 dark:text-red-300 font-medium">{e.titulo}</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${d === 0 ? "bg-red-600 text-white" : "bg-red-100 text-red-700"}`}>
                    {d === 0 ? "¡HOY!" : `${d} día${d > 1 ? "s" : ""}`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-1 flex-wrap">
          <button
            onClick={() => setFiltroTipo("todos")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filtroTipo === "todos" ? "bg-brand-navy text-white" : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
          >
            Todos
          </button>
          {(Object.keys(TIPO_CONFIG) as TipoEvento[]).map((t) => (
            <button key={t}
              onClick={() => setFiltroTipo(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filtroTipo === t ? `${TIPO_CONFIG[t].bg} ${TIPO_CONFIG[t].text} ring-1 ring-current` : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
            >
              {TIPO_CONFIG[t].label}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-xs text-gray-500 ml-auto cursor-pointer select-none">
          <input type="checkbox" checked={soloProximos} onChange={(e) => setSoloProximos(e.target.checked)} className="rounded" />
          Solo próximos
        </label>
      </div>

      {/* Lista agrupada por mes */}
      {Object.keys(porMes).length === 0 ? (
        <div className="card text-center py-12 text-gray-400">
          <Calendar size={40} className="mx-auto mb-3 opacity-20" />
          <p>No hay eventos con los filtros seleccionados.</p>
        </div>
      ) : (
        Object.entries(porMes).map(([mesKey, eventos]) => {
          const [year, month] = mesKey.split("-");
          return (
            <div key={mesKey}>
              <h3 className="text-sm font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                <span className="w-1 h-4 bg-brand-orange rounded-full inline-block" />
                {MESES[parseInt(month) - 1]} {year}
              </h3>
              <div className="space-y-3">
                {eventos.map((e) => {
                  const d = diasRestantes(e.fecha);
                  const tc = TIPO_CONFIG[e.tipo];
                  const uc = URGENCIA_CONFIG[e.urgencia];
                  const isOpen = eventoAbierto === e.id;
                  const isPast = d < 0;

                  return (
                    <div key={e.id}
                      className={`card cursor-pointer transition-all hover:shadow-md ${isPast ? "opacity-50" : ""} ${isOpen ? "ring-2 ring-brand-orange" : ""}`}
                      onClick={() => setEventoAbierto(isOpen ? null : e.id)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start gap-3 min-w-0">
                          <div className={`w-2 h-2 rounded-full ${tc.dot} mt-2 shrink-0`} />
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2 mb-0.5">
                              <span className="font-semibold text-gray-900 dark:text-white text-sm">{e.titulo}</span>
                              <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${tc.bg} ${tc.text}`}>
                                {tc.label}
                              </span>
                              {!isPast && d <= 10 && (
                                <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-700 animate-pulse">
                                  ¡{d === 0 ? "HOY" : `${d}d`}!
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-400">
                              {new Date(e.fecha + "T12:00:00").toLocaleDateString("es-CO", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
                              {e.articulo && ` · ${e.articulo}`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {uc.icon}
                          <span className="text-xs text-gray-400">
                            {isPast ? "Pasó" : d === 0 ? "Hoy" : `en ${d}d`}
                          </span>
                        </div>
                      </div>

                      {isOpen && (
                        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-slate-700">
                          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">{e.descripcion}</p>
                          {e.link && (
                            <a href={e.link} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-brand-orange hover:underline mt-2">
                              <ExternalLink size={11} /> Ver en DIAN
                            </a>
                          )}
                          <div className="mt-3 flex flex-wrap gap-2">
                            <span className={`text-xs px-2 py-1 rounded-full ${tc.bg} ${tc.text} font-medium`}>
                              {tc.label}
                            </span>
                            <span className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
                              Urgencia: {uc.label}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })
      )}

      {/* Leyenda */}
      <div className="card">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Leyenda</h3>
        <div className="flex flex-wrap gap-3">
          {(Object.entries(TIPO_CONFIG) as [TipoEvento, typeof TIPO_CONFIG[TipoEvento]][]).map(([tipo, cfg]) => (
            <span key={tipo} className={`text-xs px-3 py-1 rounded-full font-medium ${cfg.bg} ${cfg.text}`}>
              {cfg.label}
            </span>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-3">
          ⚠️ Las fechas son orientativas y pueden variar según resoluciones DIAN. Siempre verifique en{" "}
          <a href="https://www.dian.gov.co" target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">
            dian.gov.co
          </a>.
          Las fechas límite dependen del último dígito o dos dígitos del NIT del contribuyente.
        </p>
      </div>

      {/* Chatbot contextual */}
      <PageChatbot
        moduleName="Calendario DIAN"
        systemContext={DIAN_SYSTEM}
        currentData={{ eventosProximos: alertas.length, filtro: filtroTipo, hoy }}
      />
    </div>
  );
}
