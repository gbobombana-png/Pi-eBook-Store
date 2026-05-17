"""
Football AI Platform — FastAPI Backend
Analyse prédictive + détection de matchs suspects + live analysis
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .core.config import get_settings
from .core.database import init_db
from .routers import matches, analysis, live, collector

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
    except Exception as e:
        print(f"⚠️  DB init skipped (no DB available): {e}")
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="""
## Football AI Platform 🔍⚽

Plateforme d'intelligence artificielle pour l'analyse footballistique avancée.

### Modules
- **Prédiction**: Ensemble Poisson + XGBoost + Neural Network
- **Suspicion Engine**: Détection de matchs suspects (0-100)
- **Analyse des cotes**: Sharp moves, inversions, volumes anormaux
- **Live**: Probabilités recalculées minute par minute via WebSocket

### WebSocket endpoints
- `ws://.../live/ws/{match_id}` — Mises à jour live d'un match
- `ws://.../live/ws/dashboard/global` — Alertes globales
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middlewares ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(matches.router,   prefix=settings.api_v1_prefix)
app.include_router(analysis.router,  prefix=settings.api_v1_prefix)
app.include_router(live.router,      prefix=settings.api_v1_prefix)
app.include_router(collector.router, prefix=settings.api_v1_prefix)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.version,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "Football AI Platform API",
        "docs": "/docs",
        "version": settings.version,
    }
