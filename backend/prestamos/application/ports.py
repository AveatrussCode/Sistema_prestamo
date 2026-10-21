from typing import Protocol
from backend.usuarios.domain.usuario import Usuario


class UsuarioLookup(Protocol):
    def obtener_por_id(self, id_usuario: int) -> Usuario | None: ...
