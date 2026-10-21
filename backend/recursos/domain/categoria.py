from dataclasses import dataclass
from typing import Optional


@dataclass
class Categoria:
    id_categoria: int
    nombre: str
    descripcion: str = ""

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

