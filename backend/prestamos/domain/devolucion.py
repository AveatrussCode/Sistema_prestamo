

class Devolucion:
    id_devolucion: int
    fecha_devolucion: date
    estado_fisico: string
    observaciones: string



    def registrar(self, date fecha_de_retorno, string observaciones, string estado fisico) -> None:
        self.fecha_devolucion = fecha_de_retorno
        self.estado_fisico= fisico
        self.observaciones = self.observaciones

    def EvaluarEstadoFisico(self) -> None:
        self.estado_fisico= fisico

    def esta_dañado() -> none:
        self.estado_fisico= "Dañado"

    
    













