from sqlalchemy.orm import Session
from backend.usuarios.domain.rol import NombreRol, NivelRol
from backend.usuarios.infraestructure.usuario_repository import RolRepository


# Definición de los roles del sistema con sus permisos
ROLES_INICIALES = [
    {
        "nombre": NombreRol.ADMIN.value,
        "nivel": NivelRol.ALTO.value,
        "permisos": ",".join([
            "usuarios:crear", "usuarios:leer", "usuarios:actualizar",
            "usuarios:eliminar", "usuarios:cambiar_rol",
            "roles:crear", "roles:leer",
            "recursos:crear", "recursos:leer", "recursos:actualizar", "recursos:eliminar",
            "prestamos:crear", "prestamos:leer", "prestamos:actualizar",
            "prestamos:aprobar", "prestamos:rechazar", "prestamos:cancelar",
        ])
    },
    {
        "nombre": NombreRol.USUARIO_BASICO.value,
        "nivel": NivelRol.BAJO.value,
        "permisos": ",".join([
            "usuarios:leer_propio",
            "recursos:leer",
            "prestamos:crear", "prestamos:leer_propio",
        ])
    }
]


def seed_roles(db: Session):
    """Crea los roles por defecto si no existen. Es idempotente (seguro ejecutar varias veces)."""
    repo = RolRepository(db)
    creados = []
    for rol_data in ROLES_INICIALES:
        existente = repo.obtener_por_nombre(rol_data["nombre"])
        if not existente:
            nuevo = repo.guardar(
                nombre=rol_data["nombre"],
                permisos=rol_data["permisos"],
                nivel=rol_data["nivel"]
            )
            creados.append(nuevo.nombre)
            print(f"✅ Rol creado: {nuevo.nombre}")
        else:
            print(f"ℹ️  Rol ya existe: {existente.nombre}")

    if not creados:
        print("ℹ️  No se crearon roles nuevos. Todos ya existían.")
    return creados