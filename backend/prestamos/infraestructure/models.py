from sqlalchemy import Column, Date, Integer, String, ForeignKey, Index, text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.recursos.domain.enums import EstadoFisico

from backend.database import Base
from backend.prestamos.domain.reserva import EstadoReserva
from backend.prestamos.domain.enums import EstadoPrestamo


class ReservaModel(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    objeto_id = Column(Integer, nullable=False, index=True)
    fecha_reserva = Column(Date, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(
        SQLEnum(EstadoReserva),
        nullable=False,
        default=EstadoReserva.PENDIENTE,
    )


class PrestamoModel(Base):
    __tablename__ = 'prestamos'

    id = Column(Integer, primary_key=True)
    reserva_id = Column(Integer, nullable=False, unique=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    objeto_id = Column(Integer, nullable=False, index=True)
    entregado_por = Column(Integer, nullable=False)
    usuario_nombre = Column(String, nullable=False)
    objeto_nombre = Column(String, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_devolucion_prevista = Column(Date, nullable=False)
    fecha_devolucion_real = Column(Date, nullable=True)
    estado = Column(SQLEnum(EstadoPrestamo), nullable=False, default=EstadoPrestamo.ACTIVO)
    observaciones_entrega = Column(String, nullable=False, default='')
    devolucion = relationship('DevolucionModel', uselist=False, lazy='selectin')
    __table_args__ = (
        Index('uq_prestamo_activo_objeto', 'objeto_id', unique=True,
              sqlite_where=text("estado = 'ACTIVO'"), postgresql_where=text("estado = 'ACTIVO'")),
    )


class DevolucionModel(Base):
    __tablename__ = 'devoluciones'
    id = Column(Integer, primary_key=True)
    prestamo_id = Column(Integer, ForeignKey('prestamos.id'), nullable=False, unique=True)
    fecha_devolucion = Column(Date, nullable=False)
    estado_fisico = Column(SQLEnum(EstadoFisico), nullable=False)
    observaciones = Column(String, nullable=False, default='')
    recibido_por = Column(Integer, nullable=False)
