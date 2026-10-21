from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base, SessionLocal

# Modelos ANTES de create_all
from backend.usuarios.infraestructure.models import UsuarioModel, RolModel
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel
from backend.prestamos.infraestructure.models import ReservaModel

# Rutas
from backend.usuarios.presentation.usuario_routes import router as usuario_router
from backend.usuarios.presentation.rol_routes import router as rol_router
from backend.recursos.presentation.objeto_routes import router as objeto_router
from backend.recursos.presentation.categoria_routes import router as categoria_router
from backend.prestamos.presentation.reserva_routes import router as reserva_router

from backend.usuarios.infraestructure.seed_roles import seed_roles


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Préstamos API",
    description="Backend para la gestión de usuarios, recursos y préstamos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def inicializar_roles():
    db = SessionLocal()
    try:
        seed_roles(db)
    finally:
        db.close()


app.include_router(usuario_router)
app.include_router(rol_router)
app.include_router(objeto_router)
app.include_router(categoria_router)
app.include_router(reserva_router)


@app.get("/")
def read_root():
    return {"mensaje": "¡Bienvenido al backend del Sistema de Préstamos!"}