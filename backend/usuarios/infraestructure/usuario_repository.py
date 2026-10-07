from sqlalchemy.orm import Session
from backend.usuarios.domain.usuario import Estudiante, Profesor, Administrativo, Usuario
from backend.usuarios.infraestructure.models import (
    UsuarioModel, 
    EstudianteModel, 
    ProfesorModel, 
    AdministrativoModel
)

class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, usuario_domain: Usuario):
        # Convertir de Dominio a Modelo ORM según el tipo de instancia
        if isinstance(usuario_domain, Estudiante):
            db_usuario = EstudianteModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                carrera=usuario_domain.carrera,
                matricula=usuario_domain.matricula,
                tipo="estudiante"
            )
        
        elif isinstance(usuario_domain, Profesor):
            db_usuario = ProfesorModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                departamento=usuario_domain.departamento,
                especialidad=usuario_domain.especialidad,
                tipo="profesor"
            )
            
        elif isinstance(usuario_domain, Administrativo):
            db_usuario = AdministrativoModel(
                nombre=usuario_domain.nombre,
                correo_institucional=usuario_domain.correo_institucional,
                codigo_institucional=usuario_domain.codigo_institucional,
                credibilidad=usuario_domain.credibilidad,
                estado=usuario_domain.estado,
                area=usuario_domain.area,
                cargo=usuario_domain.cargo,
                tipo="administrativo"
            )
        else:
            raise ValueError("Tipo de usuario no soportado por el repositorio")

        # Guardar en la base de datos
        self.db.add(db_usuario)
        self.db.commit()
        self.db.refresh(db_usuario)
        
        # Retornar el modelo de base de datos (o podrías convertirlo de vuelta a dominio si quisieras)
        return db_usuario

    def obtener_por_correo(self, correo: str):
        # Método útil para validar si un usuario ya existe antes de crearlo
        return self.db.query(UsuarioModel).filter(UsuarioModel.correo_institucional == correo).first()