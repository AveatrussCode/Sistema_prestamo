from dataclasses import dataclass


@dataclass
class Usuario:
    id: int
    nombre: str
    correo: str
    tipo: str
    activo: bool = True