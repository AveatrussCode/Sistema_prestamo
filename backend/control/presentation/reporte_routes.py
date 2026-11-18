"""Rutas de los reportes: todo cuelga de /reportes.

main.py registra este router con dependencies=[Depends(usuario_actual)]: hay que iniciar sesión para entrar.
Quién puede ver qué se decide AQUÍ, ruta por ruta:
  - /reportes/usuario/{id}  -> cada persona ve SU reporte; el administrador ve el de cualquiera
                               (la comprobación está en reporte_usuario_routes.py).
  - /reportes/pendientes    -> solo administrador.
  - /reportes/equipo/{id}   -> solo administrador.
  - /reportes/periodo       -> solo administrador.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.control.application.reporte_pendientes_service import ReportePendientesService
from backend.control.infraestructure.sql_pendiente_devolucion_repository import SqlPendienteDevolucionRepository
from backend.control.presentation.reporte_equipo_routes import router as equipo_router
from backend.control.presentation.reporte_mensual_routes import router as mensual_router
from backend.control.presentation.reporte_usuario_routes import router as usuario_router
from backend.database import get_db
from backend.usuarios.presentation.auth_routes import administrador

router = APIRouter(prefix="/reportes", tags=["Reportes"])

# Los reportes de los demás integrantes viven en sus propios archivos y se enchufan aquí.
router.include_router(usuario_router)  # este decide por sí mismo: dueño de la cuenta o administrador
router.include_router(equipo_router, dependencies=[Depends(administrador)])
router.include_router(mensual_router, dependencies=[Depends(administrador)])


# Aquí se "cablea": se elige qué repositorio concreto (SQL) usa el servicio.
def get_reporte_pendientes_service(db: Session = Depends(get_db)) -> ReportePendientesService:
    return ReportePendientesService(SqlPendienteDevolucionRepository(db))


@router.get("/pendientes", dependencies=[Depends(administrador)])
def pendientes_de_devolucion(
    solo_vencidos: bool = Query(False),
    servicio: ReportePendientesService = Depends(get_reporte_pendientes_service),
):
    return servicio.generar(solo_vencidos)
