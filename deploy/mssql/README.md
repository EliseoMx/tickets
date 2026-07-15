# Despliegue con SQL Server

Herramientas para preparar una base de datos SQL Server para este proyecto, con o sin
Python/Django instalado en el servidor destino.

## Archivos

- **`schema.sql`** — el script recomendado. Un solo archivo T-SQL que crea **la base
  de datos, el login/usuario de la app, y todas las tablas del sistema**. No
  requiere Python ni Django instalado en el servidor destino — se ejecuta directo
  en SQL Server (con SSMS, `sqlcmd`, Azure Data Studio, etc.).
- **`bootstrap_db.ps1`** — alternativa en PowerShell que solo crea la base de datos
  y el login/usuario (no las tablas). Útil si prefieres PowerShell, o si quieres
  separar ese paso del de las tablas. Ver la sección "Crear la base de datos y el
  login automáticamente" en el README principal.
- **`generate_schema_sql.py`** — el generador que produce `schema.sql` a partir de
  las migraciones actuales de Django. Solo se usa en tu máquina de desarrollo,
  nunca en el servidor destino.
- **`documentacion_base_datos.pdf`** / **`DOCUMENTACION_TABLAS.md`** — para qué
  sirve cada tabla y cada campo, en lenguaje simple (mismo contenido en ambos
  formatos). Empieza aquí si quieres entender la base de datos sin leer código.
- **`diagrama_erd.png`** / **`diagrama_erd.svg`** — diagrama de las tablas y cómo
  se relacionan entre sí. `diagrama_erd.mmd` es el código fuente editable (formato
  [Mermaid](https://mermaid.js.org)) por si cambian las tablas y hay que
  actualizarlo — pégalo en [mermaid.live](https://mermaid.live) para editarlo y
  exportar un PNG/SVG nuevo.
- **`generate_documentation_pdf.py`** — genera `DOCUMENTACION_TABLAS.md` y
  `documentacion_base_datos.pdf` a partir de una lista de tablas/campos definida
  en el propio archivo (no lee `models.py` automáticamente — si agregas campos
  nuevos, edita la lista `TABLAS_NEGOCIO` de este script a mano y vuelve a
  correrlo).

## Flujo típico para instalar en otro servidor

1. Copia `deploy/mssql/schema.sql` al servidor destino (no hace falta copiar todo
   el proyecto todavía, ni tener Python ahí).
2. Ábrelo y **cambia la contraseña de ejemplo** que trae el `CREATE LOGIN` (cerca
   del principio del archivo). Si quieres otro nombre de base de datos o de login
   que no sea `tickets_db` / `tickets_app`, usa Buscar y Reemplazar en todo el
   archivo antes de correrlo.
3. Ejecútalo conectado a la instancia de SQL Server (con un login administrador,
   ej. `sa`), a cualquier base (ej. `master`, ya que el propio script crea y se
   cambia a la base nueva):
   - Desde SSMS: ábrelo, conéctate, y dale **Execute** (`F5`).
   - Desde PowerShell con `sqlcmd`:
     ```powershell
     sqlcmd -S localhost\SQLEXPRESS -U sa -P "<contraseña del sa>" -i deploy\mssql\schema.sql
     ```
   Esto crea la base de datos, el login/usuario, y las 19 tablas del sistema — todo
   en un solo paso. Es seguro correrlo varias veces (no falla si algo ya existe).
4. Copia el resto del proyecto (código) a ese servidor, con su propio `.env`
   apuntando a esa base (`DB_ENGINE=mssql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
   `DB_HOST`) — sin necesidad de correr `python manage.py migrate` ahí, porque
   `schema.sql` ya dejó registradas las migraciones como aplicadas.
5. Arranca la app normalmente (`waitress-serve` + IIS, o `runserver` si es de
   prueba). Ver la sección "Despliegue en Windows con IIS" del README principal.

## Regenerar `schema.sql` cuando agregues migraciones nuevas

`schema.sql` es una foto de las migraciones que existían al momento de generarlo.
Si agregas modelos/campos nuevos (nuevas migraciones), tienes que regenerarlo:

```powershell
# Con el entorno virtual activado, DB_ENGINE=mssql activo en tu .env local
python deploy/mssql/generate_schema_sql.py
```

Esto sobreescribe `deploy/mssql/schema.sql` con el esquema completo actualizado
(no solo las migraciones nuevas — el archivo completo, listo para una base vacía).

## Notas técnicas (por si el script falla algún día)

`schema.sql` se arma concatenando la salida de `python manage.py sqlmigrate` para
cada migración, en orden. Esto normalmente funciona, pero tiene dos limitaciones
conocidas del propio Django/SQL Server que el generador ya corrige automáticamente:

- **Restricciones sin nombre**: algunas migraciones base de Django (no de este
  proyecto) crean una restricción `UNIQUE`/`CHECK` de forma implícita al crear la
  tabla, sin nombre explícito — SQL Server le pone un nombre interno propio. Una
  migración posterior intenta borrarla por el nombre "esperado" y falla porque no
  existe tal cual. El generador cambia esos `DROP CONSTRAINT` por
  `DROP CONSTRAINT IF EXISTS`.
- **Índices que dependen de una columna eliminada**: si una columna se borra en una
  migración posterior a la que le creó un índice, `DROP COLUMN` falla porque el
  índice todavía depende de ella (en un `migrate` real, Django lo resuelve porque
  va viendo la base de datos viva en cada paso; aquí no hay una base viva
  todavía). El generador inserta un bloque antes de cada `DROP COLUMN` que borra
  dinámicamente cualquier índice sobre esa columna.
- La tabla `django_migrations` en sí no viene en ninguna migración (Django la crea
  aparte, fuera del sistema de migraciones) — el generador la agrega al principio
  usando el propio editor de esquema de Django.
- El bloque de `CREATE DATABASE` / `CREATE LOGIN` / `USE` / `CREATE USER` al inicio
  del archivo va separado con `GO` (SQL Server exige que `CREATE DATABASE` esté
  solo en su propio lote/batch). El resto del script (todas las tablas) sí puede
  ir en un solo batch grande. Por eso el script debe ejecutarse con una
  herramienta que entienda `GO` (SSMS o `sqlcmd`) — no funciona si lo mandas como
  un solo comando crudo por una librería que no reconozca `GO` (ej. `pyodbc`
  ejecutando el archivo completo de un jalón).

Si en el futuro `sqlmigrate` falla con un error nuevo de este mismo estilo (un
`ALTER`/`DROP` que depende de algo creado en otra migración), probablemente se
resuelve con el mismo patrón: hacer ese paso tolerante o resolverlo dinámicamente
por T-SQL, dentro de `generate_schema_sql.py`.

Probado de punta a punta contra una instancia SQL Server real, desde cero (sin la
base de datos ni el login previamente creados): el script los crea correctamente,
Django reconoce el esquema resultante como "sin migraciones pendientes" al
conectarse con el login recién creado, y el ORM puede crear/leer datos
correctamente sobre ese esquema.

## Regenerar la documentación (`DOCUMENTACION_TABLAS.md` / `documentacion_base_datos.pdf`)

Si agregas o cambias campos en `tickets/models.py`:

1. Edita la lista `TABLAS_NEGOCIO` en `generate_documentation_pdf.py` a mano
   (agrega/quita el campo correspondiente).
2. Si cambia la relación entre tablas, edita también `diagrama_erd.mmd` (pégalo en
   [mermaid.live](https://mermaid.live), ajústalo ahí, y exporta de nuevo
   `diagrama_erd.png` y `diagrama_erd.svg` con esos nombres, reemplazando los
   archivos existentes).
3. Corre:
   ```powershell
   python deploy/mssql/generate_documentation_pdf.py
   ```
   Esto regenera `DOCUMENTACION_TABLAS.md` y `documentacion_base_datos.pdf` a
   partir de la lista actualizada (y de la imagen `diagrama_erd.png` si la
   cambiaste en el paso 2).

## Pendiente: capturas de pantalla del sistema

Se pidieron capturas de pantalla (ej. la pantalla de "Crear usuario", "Crear
ticket") con anotaciones de en qué tabla/campo se guarda cada dato. No se
incluyeron en esta entrega porque la herramienta de captura de pantalla falló de
forma consistente en la sesión donde se generó este material. Si se retoma:
usar datos de prueba (prefijo `qa_`), nunca capturar pantallas con datos reales
de clientes, y limpiar los datos de prueba después.
