from abc import ABC, abstractmethod
from typing import Optional

from backend.recursos.domain.objeto import Objeto


class ObjetoRepository(ABC):

    @abstractmethod
    def guardar(self, objeto: Objeto) -> Objeto: ...

    @abstractmethod
    def buscar_por_id(self, id_objeto: int) -> Optional[Objeto]: ...

    @abstractmethod
    def listar(
        self,
        categoria_id: Optional[int] = None,
        estado: Optional[str] = None,
        busqueda: Optional[str] = None,
        solo_disponibles: bool = False,
    ) -> list[Objeto]: ...

    @abstractmethod
    def eliminar(self, id_objeto: int) -> None: ...