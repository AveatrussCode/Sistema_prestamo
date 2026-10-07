from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from backend.usuarios.domain.usuario import EstadoUsuario

from backend.database import Base

class RolModel(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    permisos = Column(String)
    nivel = Column(String)

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    correo_institucional = Column(String, unique=True, index=True)
    codigo_institucional = Column(String, unique=True)
    credibilidad = Column(Float, default=100.0)
    estado = Column(SQLEnum(EstadoUsuario), default=EstadoUsuario.ACTIVO)
    
    # Relación con Rol (Muchos a Uno según diagrama)
    rol_id = Column(Integer, ForeignKey("roles.id"))
    rol = relationship("RolModel")

    # Campo discriminador para la herencia (Single Table Inheritance)
    tipo = Column(String(50)) 
    
    # Campos específicos de subclases (deben ser nullable=True)
    carrera = Column(String, nullable=True)
    matricula = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    especialidad = Column(String, nullable=True)
    area = Column(String, nullable=True)
    cargo = Column(String, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'usuario',
        'polymorphic_on': tipo
    }

class EstudianteModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'estudiante'}

class ProfesorModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'profesor'}

class AdministrativoModel(UsuarioModel):
    __mapper_args__ = {'polymorphic_identity': 'administrativo'}