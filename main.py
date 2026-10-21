from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.shared.errors import DomainError
from backend.recursos.infrastructure.models import CategoriaModel, ObjetoModel
from backend.prestamos.infrastructure.models import ReservaModel
from backend.recursos.presentation.objeto_router import router as objeto_router, categoria_router
from backend.prestamos.presentation.reserva_routes import router as reserva_router

from backend.database import engine, Base, SessionLocal

# Importar modelos ANTES de create_all
from backend.usuarios.infraestructure.models import UsuarioModel, RolModel

# Importar rutas
from backend.usuarios.presentation.usuario_routes import router as usuario_router
from backend.usuarios.presentation.rol_routes import router as rol_router

# Importar el seed de roles
from backend.usuarios.infraestructure.seed_roles import seed_roles


# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Préstamos API",
    description="Backend para la gestión de usuarios, recursos y préstamos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def inicializar_roles():
    """Ejecuta el seed de roles al arrancar el servidor (solo crea los que faltan)."""
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()


# Rutas
app.include_router(usuario_router)
app.include_router(rol_router)
app.include_router(objeto_router)
app.include_router(categoria_router)
app.include_router(reserva_router)


@app.exception_handler(DomainError)
async def domain_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/")
def read_root():
    return {"mensaje": "¡Bienvenido al backend del Sistema de Préstamos!"}
