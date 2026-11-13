"""Rutas de los reportes: todo cuelga de /reportes.

main.py registra este router con dependencies=[Depends(administrador)],
así que TODAS las rutas de reportes (también las de los otros archivos) son solo para el administrador.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.control.application.reporte_pendientes_service import ReportePendientesService
from backend.control.infraestructure.sql_pendiente_devolucion_repository import SqlPendienteDevolucionRepository
from backend.control.presentation.reporte_equipo_routes import router as equipo_router
from backend.control.presentation.reporte_mensual_routes import router as mensual_router
from backend.control.presentation.reporte_usuario_routes import router as usuario_router
from backend.database import get_db

router = APIRouter(prefix="/reportes", tags=["Reportes"])

# Los reportes de los demás integrantes viven en sus propios archivos y se enchufan aquí.
router.include_router(usuario_router)
router.include_router(equipo_router)
router.include_router(mensual_router)


# Aquí se "cablea": se elige qué repositorio concreto (SQL) usa el servicio.
def get_reporte_pendientes_service(db: Session = Depends(get_db)) -> ReportePendientesService:
    return ReportePendientesService(SqlPendienteDevolucionRepository(db))


@router.get("/pendientes")
def pendientes_de_devolucion(
    solo_vencidos: bool = Query(False),
    servicio: ReportePendientesService = Depends(get_reporte_pendientes_service),
):
    return servicio.generar(solo_vencidos)
