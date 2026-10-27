# Base compartida en Neon

1. Crea el proyecto Neon y prueba su conexión PostgreSQL en DBeaver.
2. Guarda la URL real en `.env` como `DATABASE_URL=postgresql://...`. El backend selecciona automáticamente psycopg. No subas credenciales a Git ni las envíes por el chat. Si una contraseña se publica, cámbiala en Neon y actualiza también DBeaver.
3. Antes de migrar, detén los backends que utilicen el destino. La base de destino debe estar vacía. No arranques `main.py` antes de la primera migración porque crea roles.
4. Desde la raíz ejecuta `python -X utf8 scripts/migrar_a_postgres.py`. Crea un respaldo consistente de SQLite e inspecciona origen/destino sin modificar PostgreSQL.
5. Para copiar ejecuta `python -X utf8 scripts/migrar_a_postgres.py --aplicar`. Conserva IDs, usuarios, cuentas con hashes, catálogo, reservas, préstamos y devoluciones. No copia sesiones. Si el destino contiene registros se detiene, sin mezclar ni borrar. La copia se realiza en una transacción. Los PDF no se copian: siguen en almacenamiento local.
6. Inicia el backend con `python -X utf8 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`. Si ya estaba abierto, reinícialo para que lea la configuración nueva. Solo un integrante debe hacer la preparación inicial del esquema; después pueden arrancar los demás.
7. En DBeaver actualiza `Schemas → public → Tables`. Comprueba `SELECT COUNT(*) FROM usuarios;`. Vuelve a iniciar sesión en la aplicación.
8. Los compañeros actualizan el código, instalan `pip install -r requirements.txt` y configuran su `.env` para la misma base/rama. No vuelven a migrar SQLite. Cada uno inicia su frontend y backend.

Las reservas del mismo equipo se serializan mediante un bloqueo transaccional PostgreSQL para impedir cruces entre backends concurrentes. Las escrituras desde SQL manual pueden omitir reglas del backend: hagan las pruebas funcionales desde la aplicación.

Para verificar concurrencia, confirmación, entrega y devolución en PostgreSQL ejecuta `python -X utf8 scripts/verificar_postgres.py`. Crea un esquema temporal independiente y lo elimina al terminar, sin agregar usuarios ni equipos a las tablas compartidas.

El visor `scripts/ver_bd.py` y `scripts/respaldar_bd.py` son para SQLite. Para Neon usa DBeaver y una estrategia de respaldo PostgreSQL. Para pruebas que borran datos, usa una base o rama independiente. Los cambios futuros de columnas requieren migraciones de esquema; `create_all` no actualiza automáticamente tablas existentes.
