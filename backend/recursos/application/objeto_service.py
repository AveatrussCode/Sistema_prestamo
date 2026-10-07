


from backend.recursos.domain.enums import EstadoFisico
from backend.recursos.domain.objeto import Objeto


from backend.recursos.domain.categoria_repository import CategoriaRepository
from backend.recursos.domain.enums import EstadoFisico
from backend.recursos.domain.objeto import Objeto



class ObjetoService:

    def __init__(self, objetos: ObjetoRepository, categorias: CategoriaRepository):
        self._objetos = objetos
        self._categorias = categorias

    def registrar_objeto(self, nombre: str, descripcion: str, categoria_id: int) -> Objeto:
        categoria = self._categorias.buscar_por_id(categoria_id)
        if categoria is None:
            raise NotFoundError(f"Categoría {categoria_id} no existe.")
        if not categoria.activa:
            raise DomainError("La categoría está desactivada.")
        return self._objetos.guardar(
            Objeto(nombre=nombre.strip(), descripcion=descripcion, categoria_id=categoria_id)
        )

    def listar_objetos(self, categoria_id: Optional[int] = None,
                       solo_disponibles: bool = False) -> list[Objeto]:
        return self._objetos.listar(categoria_id, solo_disponibles)

    def obtener_objeto(self, id: int) -> Objeto:
        objeto = self._objetos.buscar_por_id(id)
        if objeto is None:
            raise NotFoundError(f"Objeto {id} no existe.")
        return objeto

    def consultar_disponibilidad(self, id: int) -> bool:
        return self.obtener_objeto(id).esta_disponible()

    def actualizar_estado_fisico(self, id: int, estado: EstadoFisico) -> Objeto:
        objeto = self.obtener_objeto(id)
        objeto.actualizar_estado_fisico(estado)
        return self._objetos.guardar(objeto)

    def dar_de_baja(self, id: int) -> Objeto:
        objeto = self.obtener_objeto(id)
        objeto.dar_de_baja()
        return self._objetos.guardar(objeto)












