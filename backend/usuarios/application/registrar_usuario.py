from backend.usuarios.domain.usuario import Estudiante, Profesor, Administrativo, EstadoUsuario

class RegistrarUsuarioUseCase:
    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def ejecutar(self, datos_usuario: dict):
        # Validaciones básicas
        if not datos_usuario.get("nombre") or not datos_usuario.get("correo"):
            raise ValueError("Nombre y correo son obligatorios")

        tipo = datos_usuario.get("tipo")
        estado_inicial = EstadoUsuario.ACTIVO
        credibilidad_inicial = 100.0

        # Lógica para crear el tipo de usuario correcto
        if tipo == "Estudiante":
            nuevo_usuario = Estudiante(
                id_usuario=None,
                nombre=datos_usuario["nombre"],
                correo=datos_usuario["correo"],
                codigo=datos_usuario["codigo"],
                credibilidad=credibilidad_inicial,
                estado=estado_inicial,
                carrera=datos_usuario.get("carrera", ""),
                matricula=datos_usuario.get("matricula", "")
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
                especialidad=datos_usuario.get("especialidad", "")
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
                cargo=datos_usuario.get("cargo", "")
            )
        else:
            raise ValueError("Tipo de usuario no válido. Debe ser: Estudiante, Profesor o Administrativo")

        # Guardar en el repositorio (Base de datos)
        return self.usuario_repository.guardar(nuevo_usuario)