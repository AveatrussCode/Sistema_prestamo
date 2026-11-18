"""Rutas del reporte por periodo (mes completo o rango de fechas). Quedan bajo /reportes/periodo.

Solo para el administrador: reporte_routes.py incluye este router con Depends(administrador).
Un "reporte mensual" es simplemente desde=día 1 y hasta=último día del mes.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.control.application.reporte_periodo_service import ReportePeriodoService
from backend.control.infraestructure.sql_periodo_reporte_repository import SqlPeriodoReporteRepository
from backend.database import get_db

router = APIRouter()


# Aquí se "cablea": se elige qué repositorio concreto (SQL) usa el servicio.
def get_reporte_periodo_service(db: Session = Depends(get_db)) -> ReportePeriodoService:
    return ReportePeriodoService(SqlPeriodoReporteRepository(db))


@router.get("/periodo")
def reporte_por_periodo(
    desde: date = Query(..., description="Primer día (AAAA-MM-DD), inclusive"),
    hasta: date = Query(..., description="Último día (AAAA-MM-DD), inclusive"),
    servicio: ReportePeriodoService = Depends(get_reporte_periodo_service),
):
    return servicio.generar(desde, hasta)
