"""PUERTO (interfaz) para obtener los datos del reporte de un usuario.

La aplicación solo conoce ESTA interfaz; quién la implementa (SQL, etc.) lo decide la infraestructura.
"""
from abc import ABC, abstractmethod

from backend.control.domain.historial_usuario import DatosUsuario, PrestamoDeUsuario, ReservaDeUsuario


class UsuarioReporteRepository(ABC):

    @abstractmethod
    def datos_de(self, id_usuario: int) -> DatosUsuario | None:
        """Datos básicos del usuario, o None si no existe."""

    @abstractmethod
    def prestamos_de(self, id_usuario: int) -> list[PrestamoDeUsuario]:
        """Todos los préstamos del usuario, del más reciente al más antiguo."""

    @abstractmethod
    def reservas_de(self, id_usuario: int) -> list[ReservaDeUsuario]:
        """Todas las reservas del usuario, de la más reciente a la más antigua."""
