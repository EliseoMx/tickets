"""
Genera deploy/mssql/schema.sql a partir de las migraciones actuales de Django.

Uso (desde la raiz del proyecto, con el entorno virtual activado):
    python deploy/mssql/generate_schema_sql.py

Vuelve a correrlo cada vez que agregues migraciones nuevas para mantener
schema.sql al dia. Requiere que DB_ENGINE=mssql este activo (en el .env o
como variable de entorno), ya que el SQL generado es especifico de SQL Server.

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

parts = []
parts.append("-- Script generado automaticamente a partir de las migraciones de Django.")
parts.append("-- Crea todas las tablas del sistema en una base de datos SQL Server vacia,")
parts.append("-- sin necesitar Python/Django instalado en ese servidor.")
parts.append("-- Ver deploy/mssql/README.md para instrucciones de uso.")
parts.append("-- Generado con: python deploy/mssql/generate_schema_sql.py")
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
