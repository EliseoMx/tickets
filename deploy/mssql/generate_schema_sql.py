"""
Genera deploy/mssql/schema.sql: un script T-SQL que crea la base de datos, el
login/usuario de la app, y todas las tablas del sistema (a partir de las
migraciones actuales de Django). El .sql resultante se ejecuta directo en
SQL Server (SSMS o sqlcmd) sin necesitar Python en el servidor destino.

Uso (desde la raiz del proyecto, con el entorno virtual activado):
    python deploy/mssql/generate_schema_sql.py

Vuelve a correrlo cada vez que agregues migraciones nuevas para mantener
schema.sql al dia. Requiere que DB_ENGINE=mssql este activo (en el .env o
como variable de entorno), ya que el SQL generado es especifico de SQL Server.

Para usar otro nombre de base de datos o de login que no sea el default
(tickets_db / tickets_app), define SCHEMA_SQL_DB_NAME / SCHEMA_SQL_APP_LOGIN
como variables de entorno antes de correr este script.

Ver deploy/mssql/README.md para instrucciones de como usar el .sql resultante.
"""
import io
import os
import re
import sys
from datetime import datetime, timezone

import django

sys.stdout.reconfigure(encoding='utf-8')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

if settings.DATABASES['default']['ENGINE'] != 'mssql':
    sys.exit(
        'DB_ENGINE debe ser "mssql" para generar este script (el SQL es especifico de '
        'SQL Server). Define DB_ENGINE=mssql en tu .env y vuelve a intentar.'
    )

connection = connections['default']
executor = MigrationExecutor(connection)
targets = executor.loader.graph.leaf_nodes()
plan = [(migration.app_label, migration.name)
        for migration, backwards in executor.migration_plan(targets, clean_start=True)]

DB_NAME = os.environ.get('SCHEMA_SQL_DB_NAME', 'tickets_db')
APP_LOGIN = os.environ.get('SCHEMA_SQL_APP_LOGIN', 'tickets_app')
APP_PASSWORD_PLACEHOLDER = 'CAMBIA_ESTA_CONTRASENA_123!'

parts = []
parts.append("-- ============================================================")
parts.append("-- Script completo: crea la base de datos, el login/usuario de")
parts.append("-- la aplicacion, y todas las tablas del sistema (a partir de")
parts.append("-- las migraciones de Django). No requiere Python/Django")
parts.append("-- instalado en el servidor destino.")
parts.append("--")
parts.append("-- ANTES DE EJECUTAR, cambia la contrasena de abajo (aparece una")
parts.append(f"-- sola vez, en el CREATE LOGIN). Si quieres otro nombre de base")
parts.append(f"-- de datos o de login, usa Buscar y Reemplazar en todo el archivo")
parts.append(f"-- para '{DB_NAME}' / '{APP_LOGIN}' antes de correrlo.")
parts.append("--")
parts.append("-- Ejecutar conectado a la instancia de SQL Server (con un login")
parts.append("-- administrador, ej. sa) desde SSMS (abrir el archivo, Execute/F5)")
parts.append("-- o sqlcmd. Es seguro de correr varias veces: si la base, el login")
parts.append("-- o las tablas ya existen, no se vuelven a crear.")
parts.append("--")
parts.append("-- Generado con: python deploy/mssql/generate_schema_sql.py")
parts.append("-- Ver deploy/mssql/README.md para mas detalles.")
parts.append("-- ============================================================")
parts.append("")
parts.append(f"IF DB_ID('{DB_NAME}') IS NULL")
parts.append("BEGIN")
parts.append(f"    CREATE DATABASE [{DB_NAME}];")
parts.append("END")
parts.append("GO")
parts.append("")
parts.append(f"IF NOT EXISTS (SELECT * FROM sys.sql_logins WHERE name = '{APP_LOGIN}')")
parts.append("BEGIN")
parts.append(f"    CREATE LOGIN [{APP_LOGIN}] WITH PASSWORD = '{APP_PASSWORD_PLACEHOLDER}', CHECK_POLICY = ON;")
parts.append("END")
parts.append("GO")
parts.append("")
parts.append(f"USE [{DB_NAME}];")
parts.append("GO")
parts.append("")
parts.append(f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{APP_LOGIN}')")
parts.append("BEGIN")
parts.append(f"    CREATE USER [{APP_LOGIN}] FOR LOGIN [{APP_LOGIN}];")
parts.append(f"    ALTER ROLE db_owner ADD MEMBER [{APP_LOGIN}];")
parts.append("END")
parts.append("GO")
parts.append("")
parts.append("-- ==== Tablas (generadas desde las migraciones de Django) ====")
parts.append("")

# django_migrations no se crea via una migracion normal (Django la crea sola,
# fuera del sistema de migraciones), asi que sqlmigrate nunca la incluye.
# La generamos aparte con el propio editor de esquema de Django.
parts.append("-- ==== django_migrations (tabla de control interna de Django) ====")
with connection.schema_editor(collect_sql=True, atomic=False) as se:
    se.create_model(MigrationRecorder.Migration)
parts.append('\n'.join(se.collected_sql))
parts.append("")

applied_rows = []
for app_label, migration_name in plan:
    buf = io.StringIO()
    call_command('sqlmigrate', app_label, migration_name, stdout=buf)
    sql = buf.getvalue().strip()
    parts.append(f"-- ==== {app_label}.{migration_name} ====")
    if sql:
        parts.append(sql)
    parts.append("")
    applied_rows.append((app_label, migration_name))

parts.append("-- ==== Registro de migraciones aplicadas (para que Django reconozca el esquema) ====")
now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
for app_label, migration_name in applied_rows:
    app_esc = app_label.replace("'", "''")
    name_esc = migration_name.replace("'", "''")
    parts.append(
        f"INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES "
        f"('{app_esc}', '{name_esc}', '{now}');"
    )

script = '\n'.join(parts) + '\n'

# Algunas restricciones UNIQUE/CHECK de las migraciones base de Django se crean
# de forma inline (sin nombre explicito) al crear la tabla, por lo que SQL Server
# les asigna un nombre interno propio distinto al que Django "cree" que tienen.
# Una migracion posterior intenta borrarlas por ese nombre esperado y falla porque
# no existe tal cual. Hacemos esos DROP tolerantes para que el script completo sea
# ejecutable de principio a fin sin intervencion manual.
script = re.sub(r'DROP CONSTRAINT \[', 'DROP CONSTRAINT IF EXISTS [', script)

# Al concatenar todas las migraciones, algunos DROP COLUMN fallan porque hay un
# indice (creado en una migracion anterior) que todavia depende de esa columna
# -- en un migrate real Django lo resuelve solo porque introspecciona la base
# viva en cada paso; aqui no hay esa base viva todavia. Antes de cada DROP COLUMN
# insertamos un bloque que borra dinamicamente cualquier indice sobre esa columna.
_drop_guard_counter = [0]


def _drop_dependent_indexes(m):
    table, column = m.group(1), m.group(2)
    _drop_guard_counter[0] += 1
    var = f"@sql_dropidx_{_drop_guard_counter[0]}"
    guard = (
        f"DECLARE {var} nvarchar(max) = '';\n"
        f"SELECT {var} = {var} + 'DROP INDEX [' + i.name + '] ON [{table}];' "
        f"FROM sys.indexes i "
        f"JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id "
        f"JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id "
        f"WHERE i.object_id = OBJECT_ID('{table}') AND c.name = '{column}' AND i.is_primary_key = 0 AND i.type > 0;\n"
        f"IF {var} <> '' EXEC({var});\n"
    )
    return guard + m.group(0)


script = re.sub(r"ALTER TABLE \[(\w+)\] DROP COLUMN \[(\w+)\];", _drop_dependent_indexes, script)

output_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'schema.sql')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(script)

print(f'OK: {len(applied_rows)} migraciones escritas en {output_path}')
