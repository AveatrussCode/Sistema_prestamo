

class CategoriaRepository():

    @abstractmethod
    def guardar(self, categoria:Categoria) -> Categoria: 
        categoria