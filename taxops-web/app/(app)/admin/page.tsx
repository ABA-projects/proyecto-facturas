"use client";

import { useState, useEffect, useCallback } from "react";
import {
  LayoutDashboard, Users, Building2, Activity, Shield,
  TrendingUp, Settings, Plus, Trash2, X, Check,
  FileText, ClipboardList, RefreshCw,
} from "lucide-react";
import { useApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";

// ── Types ─────────────────────────────────────────────────────────────────────
type User         = { id: string; email: string; full_name: string | null; role: string; active: boolean; created_at: string };
type AdminRequest = { id: string; email: string; full_name: string | null; admin_requested_at: string; created_at: string };
type Client       = { id: string; nit: string; razon_social: string; active: boolean };
type Session      = { id: string; total_archivos: number; procesados: number; errores: number; nuevas: number; duplicadas: number; status: string; started_at: string; finished_at: string | null; user_email: string | null };
type Autorreten   = { id: number; nit: string; razon_social: string | null; vigente: boolean; updated_at: string };
type Ingreso      = { id: number; periodo: string; ingresos_gravados: number; ingresos_excluidos: number; updated_at: string };
type Org          = { id: string; slug: string; name: string; nit: string | null; plan: string; active: boolean; created_at: string };
type Stats        = { total_invoices: number; total_exogenas: number; total_users: number; total_clients: number; invoices_this_month: number; recent_sessions: Session[] };

// ── Tabs ──────────────────────────────────────────────────────────────────────
const TABS = [
  { key: "dashboard",         label: "Dashboard",         icon: <LayoutDashboard size={14} /> },
  { key: "usuarios",          label: "Usuarios",          icon: <Users size={14} /> },
  { key: "solicitudes",       label: "Solicitudes Admin",  icon: <Shield size={14} /> },
  { key: "clientes",          label: "Clientes",          icon: <Building2 size={14} /> },
  { key: "actividad",         label: "Actividad",         icon: <Activity size={14} /> },
  { key: "autorretenedores",  label: "Autorretenedores",  icon: <Shield size={14} /> },
  { key: "ingresos",          label: "Ingresos",          icon: <TrendingUp size={14} /> },
  { key: "organizacion",      label: "Organización",      icon: <Settings size={14} /> },
] as const;
type TabKey = (typeof TABS)[number]["key"];

// ── Small helpers ─────────────────────────────────────────────────────────────
function Flash({ success, error }: { success: string; error: string }) {
  if (success) return <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700"><Check size={14} /> {success}</div>;
  if (error)   return <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"><X size={14} /> {error}</div>;
  return null;
}

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = { done: "bg-emerald-50 text-emerald-700", running: "bg-blue-50 text-blue-700", failed: "bg-red-50 text-red-700" };
  return <span className={`badge ${cls[status] ?? "bg-gray-100 text-gray-600"}`}>{status}</span>;
}

function COP(v: number) { return v.toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }); }

// ── Main component ────────────────────────────────────────────────────────────
export default function AdminPage() {
  const { get, post, patch, del } = useApi();
  const { user } = useAuth();
  const [tab, setTab]       = useState<TabKey>("dashboard");
  const [success, setSuccess] = useState("");
  const [error, setError]     = useState("");

  function flash(msg: string, type: "ok" | "err") {
    if (type === "ok") { setSuccess(msg); setError("");    setTimeout(() => setSuccess(""), 3500); }
    else               { setError(msg);   setSuccess(""); setTimeout(() => setError(""),   4500); }
  }

  const isOwner = user?.role === "owner";

  // ── Dashboard ──────────────────────────────────────────────────────────────
  const [stats, setStats]           = useState<Stats | null>(null);
  const [statsLoading, setStatsL]   = useState(false);
  const loadStats = useCallback(() => {
    setStatsL(true);
    get<Stats>("/admin/stats").then(setStats).catch(() => setStats(null)).finally(() => setStatsL(false));
  }, [get]);

  // ── Usuarios ───────────────────────────────────────────────────────────────
  const [users, setUsers]           = useState<User[]>([]);
  const [usersLoading, setUsersL]   = useState(false);
  const [newUser, setNewUser]       = useState({ email: "", password: "", full_name: "", role: "contador" });
  const loadUsers = useCallback(() => { setUsersL(true); get<User[]>("/admin/users").then(setUsers).finally(() => setUsersL(false)); }, [get]);

  // ── Clientes ───────────────────────────────────────────────────────────────
  const [clients, setClients]         = useState<Client[]>([]);
  const [clientsLoading, setClientsL] = useState(false);
  const [newClient, setNewClient]     = useState({ nit: "", razon_social: "" });
  const loadClients = useCallback(() => { setClientsL(true); get<Client[]>("/admin/clients").then(setClients).finally(() => setClientsL(false)); }, [get]);

  // ── Actividad ──────────────────────────────────────────────────────────────
  const [sessions, setSessions]         = useState<Session[]>([]);
  const [sessionsLoading, setSessionsL] = useState(false);
  const loadSessions = useCallback(() => { setSessionsL(true); get<Session[]>("/admin/sessions").then(setSessions).finally(() => setSessionsL(false)); }, [get]);

  // ── Autorretenedores ───────────────────────────────────────────────────────
  const [autos, setAutos]           = useState<Autorreten[]>([]);
  const [autosLoading, setAutosL]   = useState(false);
  const [newAuto, setNewAuto]       = useState({ nit: "", razon_social: "" });
  const [autoFilter, setAutoFilter] = useState("");
  const loadAutos = useCallback(() => { setAutosL(true); get<Autorreten[]>("/admin/autorretenedores").then(setAutos).finally(() => setAutosL(false)); }, [get]);

  // ── Ingresos ───────────────────────────────────────────────────────────────
  const [ingresos, setIngresos]         = useState<Ingreso[]>([]);
  const [ingresosLoading, setIngresosL] = useState(false);
  const [newIng, setNewIng]             = useState({ periodo: "", ingresos_gravados: "", ingresos_excluidos: "" });
  const loadIngresos = useCallback(() => { setIngresosL(true); get<Ingreso[]>("/admin/ingresos").then(setIngresos).finally(() => setIngresosL(false)); }, [get]);

  // ── Solicitudes Admin ─────────────────────────────────────────────────────
  const [requests, setRequests]       = useState<AdminRequest[]>([]);
  const [requestsLoading, setReqL]    = useState(false);
  const loadRequests = useCallback(() => {
    setReqL(true);
    get<AdminRequest[]>("/admin/users/admin-requests").then(setRequests).finally(() => setReqL(false));
  }, [get]);

  // ── Organización ───────────────────────────────────────────────────────────
  const [org, setOrg]             = useState<Org | null>(null);
  const [orgLoading, setOrgL]     = useState(false);
  const [orgForm, setOrgForm]     = useState({ name: "", nit: "" });
  const loadOrg = useCallback(() => {
    setOrgL(true);
    get<Org>("/admin/org")
      .then((o) => { setOrg(o); setOrgForm({ name: o.name, nit: o.nit ?? "" }); })
      .finally(() => setOrgL(false));
  }, [get]);

  // Load on tab change
  useEffect(() => {
    if (tab === "dashboard")        loadStats();
    if (tab === "usuarios")         loadUsers();
    if (tab === "solicitudes")      loadRequests();
    if (tab === "clientes")         loadClients();
    if (tab === "actividad")        loadSessions();
    if (tab === "autorretenedores") loadAutos();
    if (tab === "ingresos")         loadIngresos();
    if (tab === "organizacion")     loadOrg();
  }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Actions ────────────────────────────────────────────────────────────────
  async function createUser() {
    if (!newUser.email || !newUser.password) { flash("Email y contraseña son requeridos", "err"); return; }
    try {
      const created = await post<User>("/admin/users", newUser);
      setUsers((p) => [created, ...p]);
      setNewUser({ email: "", password: "", full_name: "", role: "contador" });
      flash("Usuario creado", "ok");
    } catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function deactivateUser(id: string) {
    try { await del(`/admin/users/${id}`); setUsers((p) => p.map((u) => u.id === id ? { ...u, active: false } : u)); flash("Usuario desactivado", "ok"); }
    catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function createClient() {
    if (!newClient.nit || !newClient.razon_social) { flash("NIT y razón social requeridos", "err"); return; }
    try {
      const created = await post<Client>("/admin/clients", newClient);
      setClients((p) => [...p, created]);
      setNewClient({ nit: "", razon_social: "" });
      flash("Cliente creado", "ok");
    } catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function addAutorretenedor() {
    if (!newAuto.nit) { flash("NIT requerido", "err"); return; }
    try { await post("/admin/autorretenedores", newAuto); setNewAuto({ nit: "", razon_social: "" }); loadAutos(); flash("NIT agregado", "ok"); }
    catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function removeAutorretenedor(nit: string) {
    try { await del(`/admin/autorretenedores/${encodeURIComponent(nit)}`); setAutos((p) => p.map((a) => a.nit === nit ? { ...a, vigente: false } : a)); flash("NIT desactivado", "ok"); }
    catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function saveIngreso() {
    if (!newIng.periodo) { flash("Periodo requerido (YYYY-MM)", "err"); return; }
    try {
      await post("/admin/ingresos", { periodo: newIng.periodo, ingresos_gravados: parseFloat(newIng.ingresos_gravados) || 0, ingresos_excluidos: parseFloat(newIng.ingresos_excluidos) || 0 });
      setNewIng({ periodo: "", ingresos_gravados: "", ingresos_excluidos: "" });
      loadIngresos();
      flash("Ingreso guardado", "ok");
    } catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function deleteIngreso(periodo: string) {
    try { await del(`/admin/ingresos/${encodeURIComponent(periodo)}`); setIngresos((p) => p.filter((i) => i.periodo !== periodo)); flash("Ingreso eliminado", "ok"); }
    catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  async function saveOrg() {
    try { await patch("/admin/org", { name: orgForm.name || undefined, nit: orgForm.nit || null }); loadOrg(); flash("Organización actualizada", "ok"); }
    catch (e: unknown) { flash(e instanceof Error ? e.message : "Error", "err"); }
  }

  const filteredAutos = autoFilter
    ? autos.filter((a) => a.nit.includes(autoFilter) || (a.razon_social ?? "").toLowerCase().includes(autoFilter.toLowerCase()))
    : autos;

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Administración</h2>
        <p className="text-gray-500 mt-1 text-sm">Gestiona usuarios, clientes, autorretenedores, ingresos de prorrateo y configuración.</p>
      </div>

      {/* Tab bar */}
      <div className="flex flex-wrap gap-1 bg-gray-100 rounded-xl p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      <Flash success={success} error={error} />

      {/* ══ DASHBOARD ══════════════════════════════════════════════════════════ */}
      {tab === "dashboard" && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900">Resumen general</h3>
            <button onClick={loadStats} className="text-gray-400 hover:text-gray-700 transition-colors" title="Actualizar"><RefreshCw size={15} /></button>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Facturas totales",     value: stats?.total_invoices,  sub: `${stats?.invoices_this_month ?? 0} este mes`, icon: <FileText size={20} className="text-brand-orange" /> },
              { label: "Registros exógenas",   value: stats?.total_exogenas,  icon: <ClipboardList size={20} className="text-blue-500" /> },
              { label: "Usuarios activos",     value: stats?.total_users,     icon: <Users size={20} className="text-emerald-500" /> },
              { label: "Clientes",             value: stats?.total_clients,   icon: <Building2 size={20} className="text-violet-500" /> },
            ].map((card) => (
              <div key={card.label} className="card flex items-start gap-3">
                <div className="p-2 bg-gray-50 rounded-lg shrink-0">{card.icon}</div>
                <div>
                  <p className="text-xs text-gray-500">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {statsLoading ? <span className="animate-pulse text-gray-300">—</span> : (card.value ?? 0).toLocaleString()}
                  </p>
                  {card.sub && <p className="text-xs text-gray-400 mt-0.5">{card.sub}</p>}
                </div>
              </div>
            ))}
          </div>
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100"><h3 className="font-semibold text-gray-900">Sesiones recientes</h3></div>
            {statsLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["Archivos","Nuevas","Errores","Estado","Fecha"].map((h) => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}
                </tr></thead>
                <tbody>
                  {(stats?.recent_sessions ?? []).map((s) => (
                    <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-6 py-3 text-gray-900">{s.total_archivos}</td>
                      <td className="px-6 py-3 text-emerald-600 font-medium">{s.nuevas}</td>
                      <td className="px-6 py-3 text-red-500">{s.errores}</td>
                      <td className="px-6 py-3"><StatusBadge status={s.status} /></td>
                      <td className="px-6 py-3 text-gray-400 text-xs">{new Date(s.started_at).toLocaleString("es-CO")}</td>
                    </tr>
                  ))}
                  {!stats?.recent_sessions?.length && <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-400 text-sm">Sin sesiones aún</td></tr>}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ══ USUARIOS ═══════════════════════════════════════════════════════════ */}
      {tab === "usuarios" && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Nuevo usuario</h3>
            <div className="grid grid-cols-2 gap-3">
              <input className="input" placeholder="Email" type="email" value={newUser.email} onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))} />
              <input className="input" placeholder="Contraseña temporal" type="password" value={newUser.password} onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))} />
              <input className="input" placeholder="Nombre completo (opcional)" value={newUser.full_name} onChange={(e) => setNewUser((p) => ({ ...p, full_name: e.target.value }))} />
              <select className="input" value={newUser.role} onChange={(e) => setNewUser((p) => ({ ...p, role: e.target.value }))}>
                <option value="contador">Contador</option>
                {isOwner && <option value="admin">Admin</option>}
                {isOwner && <option value="owner">Owner</option>}
              </select>
            </div>
            <button onClick={createUser} className="btn-primary mt-3 flex items-center gap-2"><Plus size={14} /> Crear usuario</button>
          </div>
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Usuarios ({users.length})</h3>
              <button onClick={loadUsers} className="text-gray-400 hover:text-gray-700"><RefreshCw size={14} /></button>
            </div>
            {usersLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["Email","Nombre","Rol","Estado","Último acceso",""].map((h) => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}
                </tr></thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-6 py-3 text-gray-900">{u.email}</td>
                      <td className="px-6 py-3 text-gray-500">{u.full_name ?? "—"}</td>
                      <td className="px-6 py-3">
                        <span className={`badge ${u.role === "owner" ? "bg-violet-50 text-violet-700" : u.role === "admin" ? "bg-blue-50 text-blue-700" : "bg-gray-100 text-gray-600"}`}>{u.role}</span>
                      </td>
                      <td className="px-6 py-3"><span className={`badge ${u.active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{u.active ? "Activo" : "Inactivo"}</span></td>
                      <td className="px-6 py-3 text-gray-400 text-xs">{new Date(u.created_at).toLocaleDateString("es-CO")}</td>
                      <td className="px-6 py-3 text-right">
                        {u.active && u.id !== user?.user_id && (
                          <button onClick={() => deactivateUser(u.id)} className="text-gray-400 hover:text-red-500 transition-colors" title="Desactivar"><Trash2 size={14} /></button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ══ SOLICITUDES ADMIN ══════════════════════════════════════════════════ */}
      {tab === "solicitudes" && (
        <div className="space-y-4">
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Solicitudes de acceso Admin ({requests.length})</h3>
              <button onClick={loadRequests} className="text-gray-400 hover:text-gray-700"><RefreshCw size={14} /></button>
            </div>
            {requestsLoading ? (
              <div className="p-6 text-sm text-gray-400">Cargando...</div>
            ) : requests.length === 0 ? (
              <div className="p-6 text-sm text-gray-400">No hay solicitudes pendientes.</div>
            ) : (
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["Email", "Nombre", "Solicitado", "Creado", "Acción"].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {requests.map((r) => (
                    <tr key={r.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-6 py-3 text-gray-900">{r.email}</td>
                      <td className="px-6 py-3 text-gray-500">{r.full_name ?? "—"}</td>
                      <td className="px-6 py-3 text-gray-400 text-xs">{new Date(r.admin_requested_at).toLocaleString("es-CO")}</td>
                      <td className="px-6 py-3 text-gray-400 text-xs">{new Date(r.created_at).toLocaleDateString("es-CO")}</td>
                      <td className="px-6 py-3">
                        <button
                          onClick={async () => {
                            try {
                              await post(`/admin/users/${r.id}/approve-admin`, {});
                              flash(`${r.email} promovido a admin`, "ok");
                              loadRequests();
                            } catch { flash("Error al aprobar", "err"); }
                          }}
                          className="flex items-center gap-1 bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-1 rounded-lg text-xs font-medium transition-colors"
                        >
                          <Check size={12} /> Aprobar como Admin
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ══ CLIENTES ═══════════════════════════════════════════════════════════ */}
      {tab === "clientes" && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-4">Nuevo cliente</h3>
            <div className="grid grid-cols-2 gap-3">
              <input className="input" placeholder="NIT (sin dígito de verificación)" value={newClient.nit} onChange={(e) => setNewClient((p) => ({ ...p, nit: e.target.value }))} />
              <input className="input" placeholder="Razón social" value={newClient.razon_social} onChange={(e) => setNewClient((p) => ({ ...p, razon_social: e.target.value }))} />
            </div>
            <button onClick={createClient} className="btn-primary mt-3 flex items-center gap-2"><Plus size={14} /> Agregar cliente</button>
          </div>
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Clientes ({clients.length})</h3>
              <button onClick={loadClients} className="text-gray-400 hover:text-gray-700"><RefreshCw size={14} /></button>
            </div>
            {clientsLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["NIT","Razón Social","Estado","Creado"].map((h) => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}
                </tr></thead>
                <tbody>
                  {clients.map((c) => (
                    <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-6 py-3 font-mono text-gray-700">{c.nit}</td>
                      <td className="px-6 py-3 text-gray-900">{c.razon_social}</td>
                      <td className="px-6 py-3"><span className={`badge ${c.active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{c.active ? "Activo" : "Inactivo"}</span></td>
                      <td className="px-6 py-3 text-gray-400 text-xs">{new Date((c as unknown as { created_at: string }).created_at ?? "").toLocaleDateString("es-CO")}</td>
                    </tr>
                  ))}
                  {clients.length === 0 && <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-400 text-sm">Sin clientes aún</td></tr>}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ══ ACTIVIDAD ══════════════════════════════════════════════════════════ */}
      {tab === "actividad" && (
        <div className="card p-0 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">Historial de procesamiento</h3>
              <p className="text-xs text-gray-500 mt-0.5">Últimas 100 sesiones de carga de facturas y exógenas</p>
            </div>
            <button onClick={loadSessions} className="text-gray-400 hover:text-gray-700"><RefreshCw size={14} /></button>
          </div>
          {sessionsLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["Usuario","Archivos","Procesados","Nuevas","Duplicadas","Errores","Estado","Inicio"].map((h) => <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">{h}</th>)}
                </tr></thead>
                <tbody>
                  {sessions.map((s) => (
                    <tr key={s.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500 text-xs max-w-[160px] truncate">{s.user_email ?? "—"}</td>
                      <td className="px-4 py-3 text-gray-900">{s.total_archivos}</td>
                      <td className="px-4 py-3 text-gray-700">{s.procesados}</td>
                      <td className="px-4 py-3 text-emerald-600 font-medium">{s.nuevas}</td>
                      <td className="px-4 py-3 text-gray-400">{s.duplicadas}</td>
                      <td className="px-4 py-3 text-red-500">{s.errores}</td>
                      <td className="px-4 py-3"><StatusBadge status={s.status} /></td>
                      <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">{new Date(s.started_at).toLocaleString("es-CO")}</td>
                    </tr>
                  ))}
                  {sessions.length === 0 && <tr><td colSpan={8} className="px-6 py-6 text-center text-gray-400 text-sm">Sin actividad registrada</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ══ AUTORRETENEDORES ═══════════════════════════════════════════════════ */}
      {tab === "autorretenedores" && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-1">Agregar autorretenedor</h3>
            <p className="text-sm text-gray-500 mb-4">NITs marcados como autorretenedores al procesar facturas. Se sincronizan con el extractor automáticamente.</p>
            <div className="grid grid-cols-2 gap-3">
              <input className="input" placeholder="NIT (sin dígito de verificación)" value={newAuto.nit} onChange={(e) => setNewAuto((p) => ({ ...p, nit: e.target.value }))} />
              <input className="input" placeholder="Razón social (opcional)" value={newAuto.razon_social} onChange={(e) => setNewAuto((p) => ({ ...p, razon_social: e.target.value }))} />
            </div>
            <button onClick={addAutorretenedor} className="btn-primary mt-3 flex items-center gap-2"><Plus size={14} /> Agregar NIT</button>
          </div>
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">
                  Autorretenedores — {autos.filter((a) => a.vigente).length} vigentes / {autos.length} total
                </h3>
              </div>
              <input className="input w-64 text-sm" placeholder="Buscar NIT o razón social..." value={autoFilter} onChange={(e) => setAutoFilter(e.target.value)} />
              <button onClick={loadAutos} className="text-gray-400 hover:text-gray-700 shrink-0"><RefreshCw size={14} /></button>
            </div>
            {autosLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
              <div className="max-h-[28rem] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-50 z-10">
                    <tr className="border-b border-gray-100">
                      {["NIT","Razón Social","Estado","Actualizado",""].map((h) => <th key={h} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAutos.map((a) => (
                      <tr key={a.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-6 py-2.5 font-mono text-gray-700">{a.nit}</td>
                        <td className="px-6 py-2.5 text-gray-500">{a.razon_social ?? "—"}</td>
                        <td className="px-6 py-2.5"><span className={`badge ${a.vigente ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-400"}`}>{a.vigente ? "Vigente" : "Inactivo"}</span></td>
                        <td className="px-6 py-2.5 text-gray-400 text-xs">{new Date(a.updated_at).toLocaleDateString("es-CO")}</td>
                        <td className="px-6 py-2.5 text-right">
                          {a.vigente && <button onClick={() => removeAutorretenedor(a.nit)} className="text-gray-400 hover:text-red-500 transition-colors" title="Desactivar"><Trash2 size={14} /></button>}
                        </td>
                      </tr>
                    ))}
                    {filteredAutos.length === 0 && <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-400 text-sm">Sin resultados</td></tr>}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══ INGRESOS PRORRATEO ═════════════════════════════════════════════════ */}
      {tab === "ingresos" && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-gray-900 mb-1">Registrar ingresos por periodo</h3>
            <p className="text-sm text-gray-500 mb-4">
              Usados para calcular el porcentaje de IVA deducible (Art. 490 E.T.). Si el periodo ya existe, lo sobreescribe.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Periodo</label>
                <input className="input" placeholder="2026-03" value={newIng.periodo} onChange={(e) => setNewIng((p) => ({ ...p, periodo: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Ingresos gravados $</label>
                <input className="input" type="number" min="0" placeholder="0" value={newIng.ingresos_gravados} onChange={(e) => setNewIng((p) => ({ ...p, ingresos_gravados: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Ingresos excluidos $</label>
                <input className="input" type="number" min="0" placeholder="0" value={newIng.ingresos_excluidos} onChange={(e) => setNewIng((p) => ({ ...p, ingresos_excluidos: e.target.value }))} />
              </div>
            </div>
            <button onClick={saveIngreso} className="btn-primary mt-3 flex items-center gap-2"><Plus size={14} /> Guardar periodo</button>
          </div>
          <div className="card p-0 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Ingresos registrados ({ingresos.length} periodos)</h3>
              <button onClick={loadIngresos} className="text-gray-400 hover:text-gray-700"><RefreshCw size={14} /></button>
            </div>
            {ingresosLoading ? <div className="p-6 text-sm text-gray-400">Cargando...</div> : (
              <table className="w-full text-sm">
                <thead><tr className="bg-gray-50 border-b border-gray-100">
                  {["Periodo","Gravados","Excluidos","Total","% Deducible",""].map((h, i) => <th key={h} className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase ${i > 0 ? "text-right" : "text-left"}`}>{h}</th>)}
                </tr></thead>
                <tbody>
                  {ingresos.map((i) => {
                    const total = i.ingresos_gravados + i.ingresos_excluidos;
                    const pct   = total > 0 ? ((i.ingresos_gravados / total) * 100).toFixed(1) + "%" : "—";
                    return (
                      <tr key={i.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-6 py-3 font-mono font-medium text-gray-900">{i.periodo}</td>
                        <td className="px-6 py-3 text-right text-gray-700">{COP(i.ingresos_gravados)}</td>
                        <td className="px-6 py-3 text-right text-gray-700">{COP(i.ingresos_excluidos)}</td>
                        <td className="px-6 py-3 text-right text-gray-500">{COP(total)}</td>
                        <td className="px-6 py-3 text-right font-semibold text-emerald-600">{pct}</td>
                        <td className="px-6 py-3 text-right"><button onClick={() => deleteIngreso(i.periodo)} className="text-gray-400 hover:text-red-500 transition-colors" title="Eliminar"><Trash2 size={14} /></button></td>
                      </tr>
                    );
                  })}
                  {ingresos.length === 0 && <tr><td colSpan={6} className="px-6 py-6 text-center text-gray-400 text-sm">Sin ingresos registrados</td></tr>}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* ══ ORGANIZACIÓN ═══════════════════════════════════════════════════════ */}
      {tab === "organizacion" && (
        <div className="max-w-lg space-y-4">
          {orgLoading ? <div className="text-sm text-gray-400">Cargando...</div> : org && (
            <div className="card space-y-5">
              <h3 className="font-semibold text-gray-900">Información de la organización</h3>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">Nombre de la firma</label>
                <input className="input" value={orgForm.name} onChange={(e) => setOrgForm((p) => ({ ...p, name: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-gray-500 mb-1 block">NIT de la organización</label>
                <input className="input" placeholder="Ej. 900123456" value={orgForm.nit} onChange={(e) => setOrgForm((p) => ({ ...p, nit: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-y-3 text-sm border-t border-gray-100 pt-4">
                <div className="text-gray-500">Slug</div>
                <div className="font-mono text-gray-700">{org.slug}</div>
                <div className="text-gray-500">Plan</div>
                <div><span className="badge bg-brand-orange/10 text-brand-orange capitalize">{org.plan}</span></div>
                <div className="text-gray-500">Estado</div>
                <div><span className={`badge ${org.active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{org.active ? "Activo" : "Inactivo"}</span></div>
                <div className="text-gray-500">Creado</div>
                <div className="text-gray-700">{new Date(org.created_at).toLocaleDateString("es-CO")}</div>
              </div>
              <button onClick={saveOrg} className="btn-primary flex items-center gap-2"><Check size={14} /> Guardar cambios</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

