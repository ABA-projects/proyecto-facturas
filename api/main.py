"""TaxOps FastAPI — entry point.

Estructura de imports:
  - api/ → este directorio (routers, schemas, dependencies, core/)
  - pipeline/, services/, db/, exogenas/ → directorio padre (proyecto-facturas/)

El sys.path.insert garantiza que al ejecutar `uvicorn main:app` desde api/,
el directorio raíz del proyecto quede en el path de Python.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que pipeline/, services/, db/, exogenas/ sean importables
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from routers import admin, auth, chatbot, exogenas, invoices, nomina

settings = get_settings()

app = FastAPI(
    title="TaxOps API",
    version="2.0.0",
    description="API REST para automatización contable colombiana · Facturas DIAN · Exógenas · IA",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(invoices.router)
app.include_router(exogenas.router)
app.include_router(chatbot.router)
app.include_router(admin.router)
app.include_router(nomina.router)


@app.get("/health", tags=["Health"])
async def health() -> dict:
    from db.database import db_available

    return {
        "status": "ok",
        "version": "2.0.0",
        "db": "connected" if db_available() else "unavailable",
    }
