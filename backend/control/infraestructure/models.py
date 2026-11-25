from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, Integer, String, UniqueConstraint

from backend.control.domain.enums import EstadoMovimiento
from backend.control.domain.politica_credibilidad import TipoMovimiento
from backend.database import Base


class MovimientoCredibilidadModel(Base):
    __tablename__ = "movimientos_credibilidad"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    tipo = Column(SQLEnum(TipoMovimiento), nullable=False)
    puntos = Column(Float, nullable=False)
    valor_antes = Column(Float, nullable=False)
    valor_despues = Column(Float, nullable=False)
    motivo = Column(String, nullable=False, default="")
    estado = Column(SQLEnum(EstadoMovimiento), nullable=False, default=EstadoMovimiento.APLICADO)
    prestamo_id = Column(Integer, nullable=True)
    reserva_id = Column(Integer, nullable=True)
    anula_a = Column(Integer, nullable=True)
    realizado_por = Column(Integer, nullable=True)
    fecha = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    # Un mismo hecho no se sanciona dos veces (los NULL no chocan entre sí)
    __table_args__ = (UniqueConstraint("tipo", "prestamo_id", name="uq_mov_tipo_prestamo"),
                      UniqueConstraint("tipo", "reserva_id", name="uq_mov_tipo_reserva"))
