from dataclasses import dataclass
from typing import Optional

from backend.shared.errors import DomainError


@dataclass
class Categoria:
    nombre: str
    descripcion: str = ""
    id_categoria: Optional[int] = None     # None hasta que se guarde en la base de datos
    activa: bool = True                    # permite activar() / desactivar() del diagrama

    def __post_init__(self):
        self._validar_nombre(self.nombre)

    @staticmethod
    def _validar_nombre(nombre: str) -> None:
        if not nombre or not nombre.strip():
            raise DomainError("La categoría debe tener nombre.")

    def actualizar_datos(self, nombre: str, descripcion: str) -> None:
        self._validar_nombre(nombre)
        self.nombre = nombre.strip()
        self.descripcion = descripcion

    def activar(self) -> None:
        self.activa = True

    def desactivar(self) -> None:
        self.activa = False
