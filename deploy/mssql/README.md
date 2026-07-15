# Despliegue con SQL Server

Herramientas para preparar una base de datos SQL Server para este proyecto, con o sin
Python/Django instalado en el servidor destino.

## Archivos

- **`bootstrap_db.ps1`** — crea la base de datos y un login/usuario dedicado para la
  app (si no existen). Requiere PowerShell en el servidor. Ver la sección
  "Crear la base de datos y el login automáticamente" en el README principal.
- **`schema.sql`** — crea todas las tablas del sistema. No requiere Python ni Django
  instalado en el servidor destino — se ejecuta directo en SQL Server (con SSMS,
  `sqlcmd`, Azure Data Studio, etc.).
- **`generate_schema_sql.py`** — el generador que produce `schema.sql` a partir de
  las migraciones actuales de Django. Solo se usa en tu máquina de desarrollo,
  nunca en el servidor destino.

## Flujo típico para instalar en otro servidor

1. En el servidor destino, corre `bootstrap_db.ps1` (crea la base y el login) — o
   créalos manualmente en SSMS si prefieres.
2. Ejecuta `schema.sql` contra esa base (crea todas las tablas). Puedes hacerlo:
   - Desde SSMS: abre el archivo, conéctate a la base de datos correcta (no a
     `master`), y dale **Execute** (`F5`).
   - Desde PowerShell con `sqlcmd`:
     ```powershell
     sqlcmd -S localhost\SQLEXPRESS -d tickets_db -U tickets_app -P "<contraseña>" -i deploy\mssql\schema.sql
     ```
3. Copia el proyecto (código) a ese servidor, con su propio `.env` apuntando a esa
   base (`DB_ENGINE=mssql`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`) — sin
   necesidad de correr `python manage.py migrate` ahí, porque `schema.sql` ya dejó
   registradas las migraciones como aplicadas.
4. Arranca la app normalmente (`waitress-serve` + IIS, o `runserver` si es de
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

Si en el futuro `sqlmigrate` falla con un error nuevo de este mismo estilo (un
`ALTER`/`DROP` que depende de algo creado en otra migración), probablemente se
resuelve con el mismo patrón: hacer ese paso tolerante o resolverlo dinámicamente
por T-SQL, dentro de `generate_schema_sql.py`.

Probado de punta a punta: se corrió contra una base SQL Server vacía real, se
confirmó que las tablas coinciden con las de una base creada por `migrate` normal,
que Django reconoce el esquema como "sin migraciones pendientes", y que el ORM
puede crear/leer datos correctamente sobre ese esquema.
