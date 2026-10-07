

class Prestamo:

    id_prestamo: int
    fecha_inicio: date
    fecha_devolucion_prevista: date
    estado: str
    observaciones: str

    #funcioens

    def __init__(self, id_prestamo: int, fecha_inicio: date, fecha_devolucion_prevista: date, observaciones: str = ""):
        self.id_prestamo = id_prestamo
        self.fecha_inicio = fecha_inicio
        self.fecha_devolucion_prevista = fecha_devolucion_prevista
        self.estado = EstadoPrestamo.ACTIVO
        self.observaciones = observaciones

    



