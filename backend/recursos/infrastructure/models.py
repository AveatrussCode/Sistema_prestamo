from sqlalchemy import Boolean, Column, Enum as SQLEnum, ForeignKey, Integer, String

from backend.database import Base
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico


class CategoriaModel(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    descripcion = Column(String, default="")
    activa = Column(Boolean, default=True, nullable=False)


class ObjetoModel(Base):
    __tablename__ = "objetos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, default="")
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False, index=True)
    estado_disponibilidad = Column(SQLEnum(EstadoDeDisponibilidad), nullable=False,
                                   default=EstadoDeDisponibilidad.DISPONIBLE)
    estado_fisico = Column(SQLEnum(EstadoFisico), nullable=False, default=EstadoFisico.BUENO)
