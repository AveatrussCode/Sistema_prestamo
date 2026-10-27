# Avance del sistema de préstamos EPCC

Guía de demostración. Actualizada para PostgreSQL compartido en Neon.

## Qué mostrar

El sistema conecta cuatro módulos con una base PostgreSQL compartida en Neon (o SQLite en pruebas locales): usuarios, catálogo/inventario, reservas y préstamos. El recorrido es **reserva pendiente → confirmación → entrega → préstamo activo → devolución**.

| Módulo | Avance demostrable |
| --- | --- |
| Usuarios | Registro, inicio y cierre de sesión, perfil, constancia PDF y gestión administrativa de usuarios y roles. |
| Catálogo/inventario | Alta y edición de equipos, categorías, búsqueda, filtros, ordenamiento y estados físicos y de disponibilidad. |
| Reservas | Creación, consulta propia o administrativa, confirmación, cancelación, vencimiento y rechazo de fechas cruzadas. |
| Préstamos | Entrega desde reserva confirmada, historial por usuario, plazos, devolución y bloqueo de equipos dañados. |
| Persistencia | PostgreSQL compartido en Neon, configurado por `DATABASE_URL`. Los registros se conservan al reiniciar. |

## Preparación

Desde `C:\Proyecto TI\Sistema_prestamo`, abre dos terminales si los servidores no están iniciados.

Backend:

```powershell
python -X utf8 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, en la otra terminal:

```powershell
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Abre http://127.0.0.1:5173/. Si los puertos ya están ocupados por estos servidores, utiliza la instancia existente.

Las cuentas de ejemplo existentes usan la contraseña `Epcc2026!`:

| Perfil | Correo |
| --- | --- |
| Administrativo | `lucia.ejemplo@unsa.edu.pe` |
| Estudiante | `ana.ejemplo@unsa.edu.pe` |
| Profesor | `carlos.ejemplo@unsa.edu.pe` |

Antes de presentar, comprueba la conexión Neon en DBeaver y conserva un respaldo PostgreSQL. `scripts/respaldar_bd.py` es exclusivo de SQLite. Consulta [BASE_COMPARTIDA.md](BASE_COMPARTIDA.md).

## Guion de 5 a 7 minutos

1. **Presenta el problema y los cuatro módulos.** “Centralizamos quién solicita un recurso, su disponibilidad, la reserva y la entrega y devolución físicas”.
2. **Entra como administrativo.** Muestra el inicio con cifras reales y la sección Usuarios. Explica que estudiantes y profesores no pueden gestionar cuentas ajenas.
3. **Registra un equipo desde Catálogo.** Usa un nombre reconocible, como “Laptop presentación”, una categoría y estado Bueno/Disponible. Edita su descripción para mostrar la actualización.
4. **Cierra sesión y entra como estudiante.** Muestra Mi perfil, busca el equipo y pulsa Reservar equipo. Elige **hoy** como inicio y mañana como fin para poder demostrar la entrega durante la misma presentación.
5. **Muestra la reserva pendiente.** Opcional: intenta otra reserva para el mismo equipo y las mismas fechas; el sistema la rechaza. Una fecha futura todavía no permite entregar el equipo.
6. **Entra como administrativo.** En Reservas, confirma la solicitud y pulsa Entregar equipo. Revisa usuario, equipo, fecha prevista y observaciones; confirma la entrega física.
7. **Muestra el préstamo activo.** El equipo debe figurar como Prestado en el catálogo. El estudiante puede consultar ese préstamo en Mis préstamos.
8. **Registra la devolución como administrativo.** Elige Bueno, añade observaciones y confirma. Muestra el préstamo Devuelto y el equipo disponible nuevamente.
9. **Recarga y muestra que los datos persisten.** Como variante, una devolución Dañado exige observaciones y deja el equipo No disponible para revisión.

Consejo: usa ventanas separadas de navegador o una ventana privada para mantener a la vez una sesión administrativa y otra de estudiante. Dos pestañas normales comparten la misma sesión.

## Reglas que puedes explicar

- El usuario solo consulta y cancela sus propias reservas; la administración ve el conjunto.
- No se aceptan reservas en el pasado ni con el fin anterior al inicio.
- Los extremos de las fechas están incluidos: terminar e iniciar otra reserva el mismo día cuenta como cruce.
- La creación simultánea de reservas cruzadas permite guardar solo una.
- Solo se entrega un equipo disponible, operativo y reservado por un usuario activo, dentro del período confirmado.
- Entrega y devolución actualizan sus registros y el equipo en una misma transacción. Se rechazan operaciones duplicadas.
- Un préstamo vencido sigue abierto hasta registrar la devolución. El historial indica si se devolvió fuera de plazo.
- Una reserva futura ocupa su intervalo de fechas; no marca globalmente al equipo como prestado.

## Validación reproducible

API y persistencia, en bases temporales:

```powershell
python -m unittest discover -s tests -v
```

Frontend, dentro de `frontend`:

```powershell
npm.cmd run lint
npm.cmd run build
```

Comprobación adicional con PostgreSQL configurado:

```powershell
python -X utf8 scripts/verificar_postgres.py
```

Verifica reservas simultáneas, confirmación, entrega y devolución en un esquema temporal que se elimina al terminar.

## Alcance pendiente

El frontend y backend funcionan localmente y los datos se comparten mediante Neon. No incluye envío de correos, penalizaciones automáticas por retrasos/daños, renovación de préstamos ni despliegue de producción. La constancia PDF se almacena localmente; no se valida contra un servicio universitario externo. Las políticas de préstamo existentes como clases aún no tienen una configuración administrativa integrada.

## Si algo falla durante la demostración

- Si no carga el catálogo o aparece un error de conexión, comprueba el backend en el puerto 8000 y pulsa Actualizar/Reintentar.
- Si no puedes entregar, comprueba que la reserva esté Confirmada, comience hoy o antes y no haya vencido, y que el equipo esté disponible.
- Si un equipo está Prestado, registra su devolución desde Préstamos; inventario no permite liberarlo manualmente mientras tenga un préstamo abierto.
- Si no ves el cambio después de usar otra sesión, pulsa Actualizar o vuelve a entrar en la sección.
- Comprueba que todos usen la misma base y rama de Neon. No repitas la migración sobre una base con datos.
