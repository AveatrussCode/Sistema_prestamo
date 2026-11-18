"""Rutas del reporte de equipo (quedan bajo /reportes/equipo/...).

Solo para el administrador: reporte_routes.py incluye este router con Depends(administrador).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.control.application.reporte_equipo_service import ReporteEquipoService
from backend.control.infraestructure.sql_equipo_reporte_repository import SqlEquipoReporteRepository
from backend.database import get_db

router = APIRouter()


# Aquí se "cablea": se elige qué repositorio concreto (SQL) usa el servicio.
def get_reporte_equipo_service(db: Session = Depends(get_db)) -> ReporteEquipoService:
    return ReporteEquipoService(SqlEquipoReporteRepository(db))


@router.get("/equipo/{id_equipo}")
def reporte_de_equipo(
    id_equipo: int,
    servicio: ReporteEquipoService = Depends(get_reporte_equipo_service),
):
    return servicio.generar(id_equipo)
