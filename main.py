from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base

# IMPORTANTE: Importar los modelos ANTES de create_all
from backend.usuarios.infraestructure.models import UsuarioModel, RolModel

# Importar las rutas
from backend.usuarios.presentation.usuario_routes import router as usuario_router

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Préstamos API",
    description="Backend para la gestión de usuarios, recursos y préstamos",
    version="1.0.0"
)

# CORS para el frontend (Vite corre en 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuario_router)

@app.get("/")
def read_root():
    return {"mensaje": "¡Bienvenido al backend del Sistema de Préstamos!"}