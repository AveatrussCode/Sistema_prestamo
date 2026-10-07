class Rol:
    def __init__(self, id_rol: int, nombre: str, permisos: str, nivel: str):
        self.id_rol = id_rol
        self.nombre = nombre
        self.permisos = permisos
        self.nivel = nivel

    def habilitar_permiso(self, permiso: str):
        # Lógica para añadir permisos
        self.permisos += f",{permiso}"