from backend.usuarios.domain.usuario import Usuario


def registrar_usuario(
    id: int,
    nombre: str,
    correo: str,
    tipo: str
) -> Usuario:

    usuario = Usuario(
        id=id,
        nombre=nombre,
        correo=correo,
        tipo=tipo
    )

    return usuario