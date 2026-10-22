from backend.usuarios.presentation.auth_routes import usuario_actual
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository

router = APIRouter(prefix='/usuarios', tags=['Usuarios'])
UPLOAD_DIR = Path(os.environ.get('MATRICULAS_DIR', str(Path(__file__).resolve().parents[3] / 'uploads' / 'matriculas')))
MAX_BYTES = 5 * 1024 * 1024

def constancia_path(usuario_id: int) -> Path:
    return UPLOAD_DIR / f'{usuario_id}.pdf'

def estudiante(usuario_id: int, db: Session):
    usuario = UsuarioRepository(db).obtener_por_id(usuario_id)
    if usuario is None:
        raise HTTPException(404, 'Usuario no encontrado.')
    if usuario.tipo != 'estudiante':
        raise HTTPException(400, 'La constancia solo corresponde a estudiantes.')
    return usuario

@router.put('/{usuario_id}/constancia-matricula')
async def subir_constancia(usuario_id: int, request: Request, db: Session = Depends(get_db), actor=Depends(usuario_actual)):
    if actor.id != usuario_id and (not actor.rol or actor.rol.nombre != "ADMIN"):
        raise HTTPException(403, "No puedes acceder a la constancia de otro usuario.")
    estudiante(usuario_id, db)
    if request.headers.get('content-type', '').split(';')[0] != 'application/pdf':
        raise HTTPException(415, 'Selecciona un archivo PDF.')
    contenido = bytearray()
    async for bloque in request.stream():
        if len(contenido) + len(bloque) > MAX_BYTES:
            raise HTTPException(413, 'El PDF no debe superar los 5 MB.')
        contenido.extend(bloque)
    if not contenido.startswith(b'%PDF-') or b'%%EOF' not in contenido[-1024:]:
        raise HTTPException(400, 'El archivo no tiene un formato PDF válido.')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with NamedTemporaryFile(dir=UPLOAD_DIR, suffix='.tmp', delete=False) as archivo:
            temporal = Path(archivo.name)
            archivo.write(contenido)
        os.replace(temporal, constancia_path(usuario_id))
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
    return {'mensaje': 'Constancia de matrícula guardada correctamente.'}

@router.get('/{usuario_id}/constancia-matricula')
def descargar_constancia(usuario_id: int, db: Session = Depends(get_db), actor=Depends(usuario_actual)):
    if actor.id != usuario_id and (not actor.rol or actor.rol.nombre != "ADMIN"):
        raise HTTPException(403, "No puedes acceder a la constancia de otro usuario.")
    estudiante(usuario_id, db)
    archivo = constancia_path(usuario_id)
    if not archivo.is_file():
        raise HTTPException(404, 'El estudiante todavía no tiene una constancia.')
    return FileResponse(archivo, media_type='application/pdf', filename=f'constancia-matricula-{usuario_id}.pdf')
