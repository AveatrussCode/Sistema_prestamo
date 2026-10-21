from abc import ABC, abstractmethod
from typing import Optional

from backend.recursos.domain.categoria import Categoria


class CategoriaRepository(ABC):

    @abstractmethod
    def guardar(self, categoria: Categoria) -> Categoria: ...

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Categoria]: ...

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> Optional[Categoria]: ...

    @abstractmethod
    def listar(self) -> list[Categoria]: ...