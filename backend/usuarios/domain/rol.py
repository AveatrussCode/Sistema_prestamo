from enum import Enum


class NombreRol(str, Enum):
    """Constantes de los roles disponibles en el sistema."""
    ADMIN = "ADMIN"
    USUARIO_BASICO = "USUARIO_BASICO"


class NivelRol(str, Enum):
    """Niveles jerárquicos de los roles."""
    ALTO = "ALTO"
    BAJO = "BAJO"


class Rol:
    def __init__(self, id_rol: int, nombre: str, permisos: str, nivel: str):
        self.id_rol = id_rol
        self.nombre = nombre
        self.permisos = permisos
        self.nivel = nivel

    def habilitar_permiso(self, permiso: str):
        """Añade un permiso al rol si no lo tiene ya."""
        permisos_actuales = self.permisos.split(",") if self.permisos else []
        if permiso not in permisos_actuales:
            permisos_actuales.append(permiso)
            self.permisos = ",".join(permisos_actuales)

    def revocar_permiso(self, permiso: str):
        """Quita un permiso del rol."""
        permisos_actuales = self.permisos.split(",") if self.permisos else []
        if permiso in permisos_actuales:
            permisos_actuales.remove(permiso)
            self.permisos = ",".join(permisos_actuales)

    def tiene_permiso(self, permiso: str) -> bool:
        """Verifica si el rol tiene un permiso específico."""
        permisos_actuales = self.permisos.split(",") if self.permisos else []
        return permiso in permisos_actuales or self.nivel == NivelRol.ALTO.value

    def es_admin(self) -> bool:
        """Retorna True si el rol es ADMIN."""
        return self.nombre == NombreRol.ADMIN.value