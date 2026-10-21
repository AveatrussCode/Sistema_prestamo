from abc import ABC, abstractmethod
from typing import Optional

from backend.recursos.domain.objeto import Objeto


class ObjetoRepository(ABC):

    @abstractmethod
    def guardar(self, objeto: Objeto) -> Objeto:
        """Inserta si id_objeto es None; si no, actualiza."""

    @abstractmethod
    def buscar_por_id(self, id: int) -> Optional[Objeto]: ...

    @abstractmethod
    def listar(self, categoria_id: Optional[int] = None,
               solo_disponibles: bool = False) -> list[Objeto]: ...
