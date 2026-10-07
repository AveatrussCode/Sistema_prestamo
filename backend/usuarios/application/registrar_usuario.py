from backend.usuarios.domain.usuario import Estudiante, Profesor, Administrativo, EstadoUsuario
from backend.usuarios.domain.rol import NombreRol
from backend.usuarios.infraestructure.usuario_repository import RolRepository


# Regla de negocio: qué rol por defecto le toca a cada tipo
ROL_POR_DEFECTO = {
    "Estudiante": NombreRol.USUARIO_BASICO.value,
    "Profesor": NombreRol.USUARIO_BASICO.value,
    "Administrativo": NombreRol.ADMIN.value,
}


class RegistrarUsuarioUseCase:
    def __init__(self, usuario_repository, rol_repository: RolRepository = None):
        self.usuario_repository = usuario_repository
        self.rol_repository = rol_repository

    def ejecutar(self, datos_usuario: dict):
        # Validaciones básicas
        if not datos_usuario.get("nombre") or not datos_usuario.get("correo"):
            raise ValueError("Nombre y correo son obligatorios")

        if self.usuario_repository.obtener_por_correo(datos_usuario["correo"]):
            raise ValueError("El correo ya está registrado")

        tipo = datos_usuario.get("tipo")
        estado_inicial = EstadoUsuario.ACTIVO
        credibilidad_inicial = 100.0

        # Determinar el rol a asignar (automático según el tipo)
        rol_asignado_id = self._obtener_rol_por_defecto(tipo)

        if tipo == "Estudiante":
            nuevo_usuario = Estudiante(
                id_usuario=None,
                nombre=datos_usuario["nombre"],
                correo=datos_usuario["correo"],
                codigo=datos_usuario["codigo"],
                credibilidad=credibilidad_inicial,
                estado=estado_inicial,
                carrera=datos_usuario.get("carrera", ""),
                matricula=datos_usuario.get("matricula", ""),
                rol_id=rol_asignado_id
            )
        elif tipo == "Profesor":
            nuevo_usuario = Profesor(
                id_usuario=None,
                nombre=datos_usuario["nombre"],
                correo=datos_usuario["correo"],
                codigo=datos_usuario["codigo"],
                credibilidad=credibilidad_inicial,
                estado=estado_inicial,
                departamento=datos_usuario.get("departamento", ""),
                especialidad=datos_usuario.get("especialidad", ""),
                rol_id=rol_asignado_id
            )
        elif tipo == "Administrativo":
            nuevo_usuario = Administrativo(
                id_usuario=None,
                nombre=datos_usuario["nombre"],
                correo=datos_usuario["correo"],
                codigo=datos_usuario["codigo"],
                credibilidad=credibilidad_inicial,
                estado=estado_inicial,
                area=datos_usuario.get("area", ""),
                cargo=datos_usuario.get("cargo", ""),
                rol_id=rol_asignado_id
            )
        else:
            raise ValueError("Tipo de usuario no válido. Debe ser: Estudiante, Profesor o Administrativo")

        return self.usuario_repository.guardar(nuevo_usuario)

    def _obtener_rol_por_defecto(self, tipo: str) -> int:
        """Obtiene el ID del rol por defecto según el tipo de usuario."""
        nombre_rol = ROL_POR_DEFECTO.get(tipo)
        if not nombre_rol or not self.rol_repository:
            return None
        rol = self.rol_repository.obtener_por_nombre(nombre_rol)
        return rol.id if rol else None