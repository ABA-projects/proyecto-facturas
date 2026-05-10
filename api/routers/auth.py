"""Auth router — login, refresh, me, logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError

from core.security import create_access_token, create_refresh_token, decode_token
from dependencies import get_current_user
from schemas import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    from db.auth import authenticate

    user = authenticate(body.email, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    access = create_access_token(
        sub=user["user_id"],
        org_id=user["org_id"],
        role=user["role"],
        email=user["email"],
    )
    refresh = create_refresh_token(sub=user["user_id"])
    return TokenResponse(access_token=access, refresh_token=refresh)


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
