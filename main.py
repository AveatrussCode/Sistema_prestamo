from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from backend.shared.errors import DomainError, ConflictError, NotFoundError
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base, SessionLocal

from backend.usuarios.presentation.auth_routes import router as auth_router, usuario_actual, administrador

# Modelos ANTES de create_all
from backend.usuarios.infraestructure.models import UsuarioModel, RolModel
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel
from backend.prestamos.infraestructure.models import ReservaModel

# Rutas
from backend.usuarios.presentation.usuario_routes import router as usuario_router
from backend.usuarios.presentation.rol_routes import router as rol_router
from backend.usuarios.presentation.matricula_routes import router as matricula_router
from backend.recursos.presentation.objeto_routes import router as objeto_router
from backend.recursos.presentation.categoria_routes import router as categoria_router
from backend.prestamos.presentation.reserva_routes import router as reserva_router
from backend.prestamos.presentation.prestamo_routes import router as prestamo_router

from backend.usuarios.infraestructure.seed_roles import seed_roles


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Préstamos API",
    description="Backend para la gestión de usuarios, recursos y préstamos",
    version="1.0.0",
)


@app.exception_handler(DomainError)
async def domain_error_handler(request, error):
    return JSONResponse(status_code=400, content={'detail': str(error)})


@app.exception_handler(ConflictError)
async def conflict_error_handler(request, error):
    return JSONResponse(status_code=409, content={'detail': str(error)})


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request, error):
    return JSONResponse(status_code=404, content={'detail': str(error)})

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


app.include_router(auth_router)
app.include_router(usuario_router, dependencies=[Depends(administrador)])
app.include_router(rol_router, dependencies=[Depends(administrador)])
app.include_router(matricula_router, dependencies=[Depends(usuario_actual)])
app.include_router(objeto_router, dependencies=[Depends(usuario_actual)])
app.include_router(categoria_router, dependencies=[Depends(usuario_actual)])
app.include_router(reserva_router, dependencies=[Depends(usuario_actual)])
app.include_router(prestamo_router, dependencies=[Depends(usuario_actual)])


@app.get("/")
def read_root():
    return {"mensaje": "¡Bienvenido al backend del Sistema de Préstamos!"}
