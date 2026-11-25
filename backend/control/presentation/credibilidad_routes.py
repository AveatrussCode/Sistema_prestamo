from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.control.application.credibilidad_service import CredibilidadService, ResumenCredibilidad
from backend.control.domain import politica_credibilidad as P
from backend.control.domain.movimiento_credibilidad import MovimientoCredibilidad
from backend.control.infraestructure.sql_credibilidad_repository import SqlCredibilidadRepository
from backend.database import get_db
from backend.usuarios.presentation.auth_routes import administrador, usuario_actual

router = APIRouter(prefix="/credibilidad", tags=["Credibilidad"])


def get_credibilidad_service(db: Session = Depends(get_db)) -> CredibilidadService:
    return CredibilidadService(SqlCredibilidadRepository(db))


class AjusteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valor: float | None = None          # fijar un valor exacto...
    delta: float | None = None          # ...o sumar/restar puntos
    motivo: str = Field(min_length=3, max_length=500)


class AnulacionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    motivo: str = Field(min_length=3, max_length=500)


def _mov(m: MovimientoCredibilidad) -> dict:
    return {"id": m.id, "tipo": m.tipo.value, "puntos": m.puntos, "valor_antes": m.valor_antes,
            "valor_despues": m.valor_despues, "motivo": m.motivo, "estado": m.estado.value,
            "fecha": m.fecha.isoformat(), "prestamo_id": m.prestamo_id, "reserva_id": m.reserva_id,
            "por_el_sistema": m.realizado_por is None}


def _resumen(r: ResumenCredibilidad) -> dict:
    return {"valor": r.valor, "tope": r.tope, "porcentaje": r.porcentaje,
            "nivel": r.nivel.value, "nivel_etiqueta": P.ETIQUETA[r.nivel],
            "limites": {"puede_reservar": r.limites.puede_reservar, "max_dias": r.limites.max_dias,
                        "max_equipos": r.limites.max_equipos, "anticipacion_dias": r.limites.anticipacion_dias},
            "movimientos": [_mov(m) for m in r.movimientos]}


@router.get("/mia")
def mi_credibilidad(actor=Depends(usuario_actual), servicio: CredibilidadService = Depends(get_credibilidad_service)):
    return _resumen(servicio.resumen(actor.id))


@router.get("/usuarios/{id_usuario}", dependencies=[Depends(administrador)])
def credibilidad_de(id_usuario: int, servicio: CredibilidadService = Depends(get_credibilidad_service)):
    return _resumen(servicio.resumen(id_usuario, limite=100))


@router.post("/usuarios/{id_usuario}/ajuste")
def ajustar(id_usuario: int, datos: AjusteIn, actor=Depends(administrador),
            servicio: CredibilidadService = Depends(get_credibilidad_service)):
    return _mov(servicio.ajustar(id_usuario, actor.id, datos.motivo, valor=datos.valor, delta=datos.delta))


@router.post("/movimientos/{id_movimiento}/anular")
def anular(id_movimiento: int, datos: AnulacionIn, actor=Depends(administrador),
           servicio: CredibilidadService = Depends(get_credibilidad_service)):
    return _mov(servicio.anular(id_movimiento, actor.id, datos.motivo))
