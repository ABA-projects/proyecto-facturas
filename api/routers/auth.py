"""Auth router — login, register, refresh, me, logout, Google OAuth."""
from __future__ import annotations

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError

from core.security import create_access_token, create_refresh_token, decode_token
from dependencies import get_current_user
from schemas import AccessTokenResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _slug_from_name(name: str) -> str:
    """Convert org name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug[:40] + "-" + secrets.token_hex(3)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest) -> TokenResponse:
    """Self-service registration — creates org + owner user."""
    from db.database import get_db
    from db.auth import hash_password
    from sqlalchemy import text

    try:
        with get_db() as db:
            # Check email not taken
            exists = db.execute(
                text("SELECT id FROM users WHERE email = :e"),
                {"e": body.email},
            ).fetchone()
            if exists:
                raise HTTPException(status_code=409, detail="El correo ya está registrado")

            slug = _slug_from_name(body.org_name)
            org = db.execute(
                text("""
                    INSERT INTO organizations (slug, name, plan)
                    VALUES (:s, :n, 'free')
                    RETURNING id
                """),
                {"s": slug, "n": body.org_name},
            ).mappings().fetchone()

            hashed = hash_password(body.password)
            user = db.execute(
                text("""
                    INSERT INTO users (org_id, email, hashed_password, full_name, role)
                    VALUES (:o, :e, :h, :f, 'owner')
                    RETURNING id, org_id, role, email
                """),
                {"o": org["id"], "e": body.email, "h": hashed, "f": body.full_name or ""},
            ).mappings().fetchone()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Error al crear la cuenta") from exc

    access = create_access_token(
        sub=str(user["id"]),
        org_id=str(user["org_id"]),
        role=user["role"],
        email=user["email"],
    )
    refresh = create_refresh_token(sub=str(user["id"]))
    return TokenResponse(access_token=access, refresh_token=refresh)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_login(request: Request) -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    from core.config import get_settings
    s = get_settings()
    if not s.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth no configurado")

    state = secrets.token_urlsafe(16)
    redirect_uri = f"{s.APP_BASE_URL}/api/auth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={s.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=select_account"
    )
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str, state: str | None = None) -> dict:
    """Exchange Google code for tokens, create/find user, return JWT."""
    import httpx
    from core.config import get_settings
    from db.database import get_db
    from db.auth import hash_password
    from sqlalchemy import text

    s = get_settings()
    if not s.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth no configurado")

    redirect_uri = f"{s.APP_BASE_URL}/api/auth/google/callback"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": s.GOOGLE_CLIENT_ID,
                "client_secret": s.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if not token_res.is_success:
        raise HTTPException(status_code=400, detail="Error al autenticar con Google")

    id_token_str = token_res.json().get("id_token", "")

    # Decode the ID token (without verification for simplicity — Google validates code exchange)
    import base64, json as _json
    try:
        payload_b64 = id_token_str.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        google_user = _json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        raise HTTPException(status_code=400, detail="Token de Google inválido")

    email = google_user.get("email", "").lower()
    full_name = google_user.get("name", "")
    if not email:
        raise HTTPException(status_code=400, detail="Google no proporcionó email")

    try:
        with get_db() as db:
            row = db.execute(
                text("SELECT id, org_id, role, email FROM users WHERE email = :e AND active = TRUE"),
                {"e": email},
            ).mappings().fetchone()

            if row is None:
                # Auto-register: create org + owner user
                slug = _slug_from_name(full_name or email.split("@")[0])
                org_name = full_name or email.split("@")[0]
                org = db.execute(
                    text("INSERT INTO organizations (slug, name, plan) VALUES (:s, :n, 'free') RETURNING id"),
                    {"s": slug, "n": org_name},
                ).mappings().fetchone()
                row = db.execute(
                    text("""
                        INSERT INTO users (org_id, email, hashed_password, full_name, role)
                        VALUES (:o, :e, :h, :f, 'owner')
                        RETURNING id, org_id, role, email
                    """),
                    {"o": org["id"], "e": email, "h": hash_password(secrets.token_hex(16)), "f": full_name},
                ).mappings().fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Error de base de datos") from exc

    access = create_access_token(
        sub=str(row["id"]),
        org_id=str(row["org_id"]),
        role=row["role"],
        email=row["email"],
    )
    refresh = create_refresh_token(sub=str(row["id"]))

    # Redirect to frontend with tokens in query params (frontend reads & stores them)
    frontend_url = f"{s.APP_BASE_URL}/auth/callback?access_token={access}&refresh_token={refresh}"
    return RedirectResponse(frontend_url)



@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(body: RefreshRequest) -> AccessTokenResponse:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token de refresco inválido")
        user_id = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

    from db.database import get_db
    from sqlalchemy import text

    try:
        with get_db() as db:
            row = db.execute(
                text(
                    "SELECT id, org_id, role, email FROM users "
                    "WHERE id = :id AND active = TRUE"
                ),
                {"id": user_id},
            ).mappings().fetchone()
    except Exception:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    if row is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

    access = create_access_token(
        sub=str(row["id"]),
        org_id=str(row["org_id"]),
        role=row["role"],
        email=row["email"],
    )
    return AccessTokenResponse(access_token=access)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    from db.database import get_db
    from sqlalchemy import text

    try:
        with get_db() as db:
            row = db.execute(
                text(
                    "SELECT id, org_id, email, full_name, role, active, "
                    "last_login_at, created_at FROM users WHERE id = :id"
                ),
                {"id": user["user_id"]},
            ).mappings().fetchone()
    except Exception:
        raise HTTPException(status_code=503, detail="Base de datos no disponible")

    if row is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

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


@router.post("/logout")
async def logout() -> dict:
    # JWT es stateless; el cliente descarta los tokens
    return {"message": "Sesión cerrada"}
