from backend.usuarios.domain.usuario import EstadoUsuario


class GestionarPerfilUseCase:
    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def actualizar_perfil(self, id_usuario: int, datos: dict):
        """Actualiza nombre y correo de un usuario existente."""
        usuario = self.usuario_repository.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        # Si cambia el correo, validar que no exista ya en otro usuario
        nuevo_correo = datos.get("correo")
        if nuevo_correo and nuevo_correo != usuario.correo_institucional:
            existente = self.usuario_repository.obtener_por_correo(nuevo_correo)
            if existente and existente.id != id_usuario:
                raise ValueError("El correo ya está registrado por otro usuario")

        campos_actualizables = ["nombre", "correo"]
        return self.usuario_repository.actualizar(id_usuario, {
            k: v for k, v in datos.items() if k in campos_actualizables and v is not None
        })

    def cambiar_estado(self, id_usuario: int, nuevo_estado: str):
        """Cambia el estado de un usuario: ACTIVO, INACTIVO, SUSPENDIDO."""
        usuario = self.usuario_repository.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        # Validar que el estado sea válido
        estados_validos = [e.value for e in EstadoUsuario]
        if nuevo_estado not in estados_validos:
            raise ValueError(
                f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
            )

        return self.usuario_repository.actualizar_estado(id_usuario, nuevo_estado)

    def eliminar_usuario(self, id_usuario: int):
        """Elimina un usuario de la base de datos."""
        usuario = self.usuario_repository.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        return self.usuario_repository.eliminar(id_usuario)


class GestionarCredibilidadUseCase:
    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def ajustar_credibilidad(self, id_usuario: int, delta: float, motivo: str = ""):
        """
        Ajusta la credibilidad de un usuario sumando o restando puntos.
        delta: puede ser positivo (subir) o negativo (bajar).
        La credibilidad resultante debe estar entre 0 y 100.
        """
        if not motivo or not motivo.strip():
            raise ValueError("El motivo del ajuste es obligatorio")

        usuario = self.usuario_repository.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        nueva_credibilidad = usuario.credibilidad + delta

        if nueva_credibilidad < 0:
            nueva_credibilidad = 0.0
        elif nueva_credibilidad > 100:
            nueva_credibilidad = 100.0

        return self.usuario_repository.actualizar_credibilidad(
            id_usuario, nueva_credibilidad
        )

    def establecer_credibilidad(self, id_usuario: int, valor: float, motivo: str = ""):
        """Establece un valor específico de credibilidad (0-100)."""
        if valor < 0 or valor > 100:
            raise ValueError("La credibilidad debe estar entre 0 y 100")

        if not motivo or not motivo.strip():
            raise ValueError("El motivo del ajuste es obligatorio")

        usuario = self.usuario_repository.obtener_por_id(id_usuario)
        if not usuario:
            raise ValueError(f"Usuario con id {id_usuario} no encontrado")

        return self.usuario_repository.actualizar_credibilidad(id_usuario, valor)