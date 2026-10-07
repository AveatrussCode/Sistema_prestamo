class AsignarRolUseCase:
    def __init__(self, usuario_repository):
        self.usuario_repository = usuario_repository

    def ejecutar(self, id_usuario: int, id_rol: int):
        return self.usuario_repository.asignar_rol(id_usuario, id_rol)