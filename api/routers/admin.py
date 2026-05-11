"""Admin router — stats, users CRUD, clients, superadmin."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from dependencies import get_current_user, require_admin, require_superadmin
from schemas import (
    AdminStats,
    ClientResponse,
    CreateClientRequest,
    CreateOrgRequest,
    CreateUserRequest,
    OrgResponse,
    SuperadminOrgStats,
    UpdateUserRequest,
    UserResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


def _get_db():
    from db.database import db_available, get_db

    if not db_available():
        raise HTTPException(status_code=503, detail="Base de datos no disponible")
    return get_db


# ── Dashboard stats ───────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
async def get_stats(user: dict = Depends(require_admin)) -> AdminStats:
    get_db = _get_db()
    org = user["org_id"]

    try:
        with get_db() as db:
            total_inv = db.execute(
                text("SELECT COUNT(*) FROM invoices WHERE org_id = :o"), {"o": org}
            ).scalar() or 0
            total_exo = db.execute(
                text("SELECT COUNT(*) FROM exogenas_results WHERE org_id = :o"), {"o": org}
            ).scalar() or 0
            total_usr = db.execute(
                text("SELECT COUNT(*) FROM users WHERE org_id = :o"), {"o": org}
            ).scalar() or 0
            total_cli = db.execute(
                text("SELECT COUNT(*) FROM clients WHERE org_id = :o"), {"o": org}
            ).scalar() or 0
            this_month = db.execute(
                text(
                    "SELECT COUNT(*) FROM invoices WHERE org_id = :o "
                    "AND periodo = TO_CHAR(NOW(), 'YYYY-MM')"
                ),
                {"o": org},
            ).scalar() or 0
            sessions = db.execute(
                text(
                    "SELECT id, total_archivos, nuevas, errores, status, started_at "
                    "FROM processing_sessions WHERE org_id = :o "
                    "ORDER BY started_at DESC LIMIT 10"
                ),
                {"o": org},
            ).mappings().fetchall()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return AdminStats(
        total_invoices=total_inv,
        total_exogenas=total_exo,
        total_users=total_usr,
        total_clients=total_cli,
        invoices_this_month=this_month,
        recent_sessions=[dict(s) for s in sessions],
    )


# ── Users ────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def list_users(user: dict = Depends(require_admin)) -> list[UserResponse]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text(
                "SELECT id, org_id, email, full_name, role, active, last_login_at, created_at "
                "FROM users WHERE org_id = :o ORDER BY created_at DESC"
            ),
            {"o": user["org_id"]},
        ).mappings().fetchall()
    return [
        UserResponse(
            id=str(r["id"]),
            org_id=str(r["org_id"]),
            email=r["email"],
            full_name=r["full_name"],
            role=r["role"],
            active=r["active"],
            last_login_at=r["last_login_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin: dict = Depends(require_admin),
) -> UserResponse:
    from db.auth import hash_password

    get_db = _get_db()
    hashed = hash_password(body.password)

    try:
        with get_db() as db:
            row = db.execute(
                text(
                    "INSERT INTO users (org_id, email, hashed_password, full_name, role) "
                    "VALUES (:org_id, :email, :hp, :fn, :role) "
                    "RETURNING id, org_id, email, full_name, role, active, last_login_at, created_at"
                ),
                {
                    "org_id": admin["org_id"],
                    "email": body.email,
                    "hp": hashed,
                    "fn": body.full_name,
                    "role": body.role,
                },
            ).mappings().fetchone()
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Email ya registrado")
        raise HTTPException(status_code=500, detail=str(exc))

    return UserResponse(
        id=str(row["id"]),
        org_id=str(row["org_id"]),
        email=row["email"],
        full_name=row["full_name"],
        role=row["role"],
        active=row["active"],
        last_login_at=row["last_login_at"],
        created_at=row["created_at"],
    )


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    admin: dict = Depends(require_admin),
) -> dict:
    get_db = _get_db()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="Sin cambios que aplicar")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["_user_id"] = user_id
    updates["_org_id"] = admin["org_id"]

    with get_db() as db:
        db.execute(
            text(f"UPDATE users SET {set_clause} WHERE id = :_user_id AND org_id = :_org_id"),
            updates,
        )
    return {"message": "Usuario actualizado"}


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(require_admin),
) -> dict:
    get_db = _get_db()
    with get_db() as db:
        db.execute(
            text("UPDATE users SET active = FALSE WHERE id = :id AND org_id = :o"),
            {"id": user_id, "o": admin["org_id"]},
        )
    return {"message": "Usuario desactivado"}


@router.get("/users/admin-requests")
async def list_admin_requests(admin: dict = Depends(require_admin)) -> list[dict]:
    """Lista contadores que han solicitado ser promovidos a admin."""
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text("""
                SELECT id, email, full_name, admin_requested_at, created_at
                FROM users
                WHERE org_id = :o AND role = 'contador'
                  AND admin_requested_at IS NOT NULL
                  AND active = TRUE
                ORDER BY admin_requested_at ASC
            """),
            {"o": admin["org_id"]},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/users/{user_id}/approve-admin")
async def approve_admin(
    user_id: str,
    admin: dict = Depends(require_admin),
) -> dict:
    """Promueve un contador a admin y limpia la solicitud."""
    get_db = _get_db()
    with get_db() as db:
        result = db.execute(
            text("""
                UPDATE users
                SET role = 'admin', admin_requested_at = NULL
                WHERE id = :id AND org_id = :o AND role = 'contador'
                RETURNING id
            """),
            {"id": user_id, "o": admin["org_id"]},
        ).fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o ya es admin")
    return {"message": "Usuario promovido a admin"}


# ── Clients ──────────────────────────────────────────────────────────────────

@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(user: dict = Depends(require_admin)) -> list[ClientResponse]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text(
                "SELECT id, org_id, nit, razon_social, active, created_at "
                "FROM clients WHERE org_id = :o ORDER BY razon_social"
            ),
            {"o": user["org_id"]},
        ).mappings().fetchall()
    return [
        ClientResponse(
            id=str(r["id"]),
            org_id=str(r["org_id"]),
            nit=r["nit"],
            razon_social=r["razon_social"],
            active=r["active"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/clients", response_model=ClientResponse, status_code=201)
async def create_client(
    body: CreateClientRequest,
    admin: dict = Depends(require_admin),
) -> ClientResponse:
    get_db = _get_db()
    try:
        with get_db() as db:
            row = db.execute(
                text(
                    "INSERT INTO clients (org_id, nit, razon_social) "
                    "VALUES (:o, :nit, :rs) "
                    "RETURNING id, org_id, nit, razon_social, active, created_at"
                ),
                {"o": admin["org_id"], "nit": body.nit, "rs": body.razon_social},
            ).mappings().fetchone()
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="NIT ya registrado en esta organización")
        raise HTTPException(status_code=500, detail=str(exc))

    return ClientResponse(
        id=str(row["id"]),
        org_id=str(row["org_id"]),
        nit=row["nit"],
        razon_social=row["razon_social"],
        active=row["active"],
        created_at=row["created_at"],
    )


# ── Superadmin ────────────────────────────────────────────────────────────────

@router.get("/superadmin/orgs", response_model=list[SuperadminOrgStats])
async def list_orgs(_: dict = Depends(require_superadmin)) -> list[SuperadminOrgStats]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text(
                "SELECT o.id, o.slug, o.name, o.plan, o.active, "
                "COUNT(DISTINCT u.id) AS users_count, "
                "COUNT(DISTINCT i.id) AS invoices_count "
                "FROM organizations o "
                "LEFT JOIN users u ON u.org_id = o.id "
                "LEFT JOIN invoices i ON i.org_id = o.id "
                "GROUP BY o.id ORDER BY o.created_at DESC"
            )
        ).mappings().fetchall()
    return [
        SuperadminOrgStats(
            id=str(r["id"]),
            slug=r["slug"],
            name=r["name"],
            plan=r["plan"],
            active=r["active"],
            users_count=r["users_count"],
            invoices_count=r["invoices_count"],
        )
        for r in rows
    ]


@router.post("/superadmin/orgs", response_model=OrgResponse, status_code=201)
async def create_org(
    body: CreateOrgRequest,
    _: dict = Depends(require_superadmin),
) -> OrgResponse:
    get_db = _get_db()
    try:
        with get_db() as db:
            row = db.execute(
                text(
                    "INSERT INTO organizations (slug, name, nit, plan) "
                    "VALUES (:slug, :name, :nit, :plan) "
                    "RETURNING id, slug, name, nit, plan, active, created_at"
                ),
                body.model_dump(),
            ).mappings().fetchone()
    except Exception as exc:
        if "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Slug ya existe")
        raise HTTPException(status_code=500, detail=str(exc))

    return OrgResponse(
        id=str(row["id"]),
        slug=row["slug"],
        name=row["name"],
        nit=row["nit"],
        plan=row["plan"],
        active=row["active"],
        created_at=row["created_at"],
    )


# ── Sessions / Actividad ──────────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(user: dict = Depends(require_admin)) -> list[dict]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text("""
                SELECT ps.id, ps.total_archivos, ps.procesados, ps.errores,
                       ps.nuevas, ps.duplicadas, ps.status,
                       ps.started_at, ps.finished_at,
                       u.email AS user_email
                FROM processing_sessions ps
                LEFT JOIN users u ON u.id = ps.user_id
                WHERE ps.org_id = :o
                ORDER BY ps.started_at DESC
                LIMIT 100
            """),
            {"o": user["org_id"]},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


# ── Autorretenedores ──────────────────────────────────────────────────────────

@router.get("/autorretenedores")
async def list_autorretenedores(user: dict = Depends(require_admin)) -> list[dict]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text("SELECT id, nit, razon_social, vigente, updated_at FROM autorretenedores ORDER BY nit")
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/autorretenedores", status_code=201)
async def add_autorretenedor(body: dict, admin: dict = Depends(require_admin)) -> dict:
    nit = (body.get("nit") or "").strip()
    razon_social = (body.get("razon_social") or "").strip() or None
    if not nit:
        raise HTTPException(status_code=422, detail="NIT requerido")
    get_db = _get_db()
    try:
        with get_db() as db:
            db.execute(
                text(
                    "INSERT INTO autorretenedores (nit, razon_social) VALUES (:nit, :rs) "
                    "ON CONFLICT (nit) DO UPDATE SET vigente = TRUE, razon_social = EXCLUDED.razon_social, updated_at = NOW()"
                ),
                {"nit": nit, "rs": razon_social},
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"nit": nit, "message": "Autorretenedor agregado"}


@router.delete("/autorretenedores/{nit}")
async def remove_autorretenedor(nit: str, admin: dict = Depends(require_admin)) -> dict:
    get_db = _get_db()
    with get_db() as db:
        db.execute(
            text("UPDATE autorretenedores SET vigente = FALSE, updated_at = NOW() WHERE nit = :nit"),
            {"nit": nit},
        )
    return {"message": "NIT desactivado"}


# ── Ingresos prorrateo ────────────────────────────────────────────────────────

@router.get("/ingresos")
async def list_ingresos(user: dict = Depends(require_admin)) -> list[dict]:
    get_db = _get_db()
    with get_db() as db:
        rows = db.execute(
            text(
                "SELECT id, periodo, ingresos_gravados, ingresos_excluidos, updated_at "
                "FROM ingresos_prorateo WHERE org_id = :o ORDER BY periodo DESC"
            ),
            {"o": user["org_id"]},
        ).mappings().fetchall()
    return [dict(r) for r in rows]


@router.post("/ingresos", status_code=201)
async def upsert_ingreso(body: dict, admin: dict = Depends(require_admin)) -> dict:
    periodo = (body.get("periodo") or "").strip()
    if not periodo:
        raise HTTPException(status_code=422, detail="Periodo requerido (YYYY-MM)")
    gravados = float(body.get("ingresos_gravados") or 0)
    excluidos = float(body.get("ingresos_excluidos") or 0)
    get_db = _get_db()
    with get_db() as db:
        db.execute(
            text(
                "INSERT INTO ingresos_prorateo (org_id, periodo, ingresos_gravados, ingresos_excluidos) "
                "VALUES (:o, :p, :g, :e) "
                "ON CONFLICT (org_id, periodo) DO UPDATE "
                "SET ingresos_gravados = EXCLUDED.ingresos_gravados, "
                "    ingresos_excluidos = EXCLUDED.ingresos_excluidos"
            ),
            {"o": admin["org_id"], "p": periodo, "g": gravados, "e": excluidos},
        )
    return {"periodo": periodo, "message": "Ingreso guardado"}


@router.delete("/ingresos/{periodo}")
async def delete_ingreso(periodo: str, admin: dict = Depends(require_admin)) -> dict:
    get_db = _get_db()
    with get_db() as db:
        db.execute(
            text("DELETE FROM ingresos_prorateo WHERE org_id = :o AND periodo = :p"),
            {"o": admin["org_id"], "p": periodo},
        )
    return {"message": "Ingreso eliminado"}


# ── Organización propia ───────────────────────────────────────────────────────

@router.get("/org")
async def get_org(user: dict = Depends(require_admin)) -> dict:
    get_db = _get_db()
    with get_db() as db:
        row = db.execute(
            text("SELECT id, slug, name, nit, plan, active, created_at FROM organizations WHERE id = :o"),
            {"o": user["org_id"]},
        ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return dict(row)


@router.patch("/org")
async def update_org(body: dict, admin: dict = Depends(require_admin)) -> dict:
    allowed = {"name", "nit"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if not updates:
        raise HTTPException(status_code=422, detail="Sin cambios válidos")
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["_org_id"] = admin["org_id"]
    get_db = _get_db()
    with get_db() as db:
        db.execute(
            text(f"UPDATE organizations SET {set_clause} WHERE id = :_org_id"),
            updates,
        )
    return {"message": "Organización actualizada"}
