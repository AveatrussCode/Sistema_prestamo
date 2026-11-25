"""Reglas de credibilidad. Archivo PURO: sin base de datos, sin FastAPI. Aquí viven los números."""
from dataclasses import dataclass
from enum import Enum


class Nivel(str, Enum):
    RESTRINGIDO = "RESTRINGIDO"
    EN_OBSERVACION = "EN_OBSERVACION"
    ESTANDAR = "ESTANDAR"
    CONFIABLE = "CONFIABLE"
    EJEMPLAR = "EJEMPLAR"


class TipoMovimiento(str, Enum):
    DEVOLUCION_PUNTUAL = "DEVOLUCION_PUNTUAL"
    DEVOLUCION_TARDIA = "DEVOLUCION_TARDIA"
    EQUIPO_REGULAR = "EQUIPO_REGULAR"
    EQUIPO_DANADO = "EQUIPO_DANADO"
    RESERVA_NO_RECOGIDA = "RESERVA_NO_RECOGIDA"
    CANCELACION_TARDIA = "CANCELACION_TARDIA"
    AJUSTE_ADMIN = "AJUSTE_ADMIN"
    ANULACION = "ANULACION"


@dataclass(frozen=True)
class Escala:
    inicio: float
    tope: float

    @property
    def factor(self) -> float:          # los puntos del personal valen el doble
        return self.tope / 100


ESCALAS = {"estudiante": Escala(50, 100), "profesor": Escala(100, 200), "administrativo": Escala(100, 200)}

# (nivel, porcentaje mínimo): se recorre de mayor a menor
UMBRALES = [(Nivel.EJEMPLAR, 90), (Nivel.CONFIABLE, 70), (Nivel.ESTANDAR, 40),
            (Nivel.EN_OBSERVACION, 20), (Nivel.RESTRINGIDO, 0)]
TECHO_AUTOMATICO_PCT = 69        # la subida automática no pasa de aquí

# Puntos en escala de 100 (se multiplican por escala.factor)
PUNTOS_PUNTUAL, MAX_BONO_SEMANAL = 3, 6
PUNTOS_POR_DIA_TARDE, MAX_TARDE = 3, 15
PUNTOS_REGULAR, PUNTOS_DANADO = 5, 15
PUNTOS_NO_RECOGIDA, PUNTOS_CANCELACION_TARDIA = 5, 2


@dataclass(frozen=True)
class Limites:
    puede_reservar: bool
    max_dias: int
    max_equipos: int
    anticipacion_dias: int


# Grupo "personal" = profesor y administrativo (se separan después si hace falta)
_LIMITES = {
    "estudiante": {Nivel.RESTRINGIDO: (0, 0), Nivel.EN_OBSERVACION: (1, 1), Nivel.ESTANDAR: (2, 1),
                   Nivel.CONFIABLE: (3, 2), Nivel.EJEMPLAR: (5, 3)},
    "personal":   {Nivel.RESTRINGIDO: (0, 0), Nivel.EN_OBSERVACION: (1, 1), Nivel.ESTANDAR: (3, 3),
                   Nivel.CONFIABLE: (5, 4), Nivel.EJEMPLAR: (7, 6)},
}
_ANTICIPACION = {"estudiante": 7, "personal": 30}


def grupo(tipo: str) -> str:
    return "estudiante" if tipo == "estudiante" else "personal"


def escala(tipo: str) -> Escala:
    return ESCALAS.get(tipo, ESCALAS["profesor"])


def porcentaje(valor: float, tipo: str) -> float:
    return valor * 100 / escala(tipo).tope


def nivel(valor: float, tipo: str) -> Nivel:
    pct = porcentaje(valor, tipo)
    return next(n for n, minimo in UMBRALES if pct >= minimo)


def limites(valor: float, tipo: str) -> Limites:
    n, g = nivel(valor, tipo), grupo(tipo)
    dias, equipos = _LIMITES[g][n]
    anticipacion = 0 if n == Nivel.EN_OBSERVACION else _ANTICIPACION[g]
    return Limites(n != Nivel.RESTRINGIDO, dias, equipos, anticipacion)


def techo_automatico(tipo: str) -> float:
    return escala(tipo).tope * TECHO_AUTOMATICO_PCT / 100


def puntos_devolucion_tardia(dias_tarde: int, tipo: str) -> float:
    return -min(dias_tarde * PUNTOS_POR_DIA_TARDE, MAX_TARDE) * escala(tipo).factor


def puntos(tipo_mov: TipoMovimiento, tipo_usuario: str) -> float:
    base = {TipoMovimiento.DEVOLUCION_PUNTUAL: PUNTOS_PUNTUAL, TipoMovimiento.EQUIPO_REGULAR: -PUNTOS_REGULAR,
            TipoMovimiento.EQUIPO_DANADO: -PUNTOS_DANADO, TipoMovimiento.RESERVA_NO_RECOGIDA: -PUNTOS_NO_RECOGIDA,
            TipoMovimiento.CANCELACION_TARDIA: -PUNTOS_CANCELACION_TARDIA}[tipo_mov]
    return base * escala(tipo_usuario).factor


def limitar_subida(actual: float, delta: float, tipo: str) -> float:
    """Una subida AUTOMÁTICA nunca pasa del techo (69%). Las bajadas no se tocan."""
    if delta <= 0:
        return delta
    return max(0.0, min(delta, techo_automatico(tipo) - actual))


def acotar(valor: float, tipo: str) -> float:
    return max(0.0, min(valor, escala(tipo).tope))


ETIQUETA = {Nivel.RESTRINGIDO: "Restringido", Nivel.EN_OBSERVACION: "En observación",
            Nivel.ESTANDAR: "Estándar", Nivel.CONFIABLE: "Confiable", Nivel.EJEMPLAR: "Ejemplar"}
