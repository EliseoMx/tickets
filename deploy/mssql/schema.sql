-- ============================================================
-- Script completo: crea la base de datos, el login/usuario de
-- la aplicacion, y todas las tablas del sistema (a partir de
-- las migraciones de Django). No requiere Python/Django
-- instalado en el servidor destino.
--
-- ANTES DE EJECUTAR, cambia la contrasena de abajo (aparece una
-- sola vez, en el CREATE LOGIN). Si quieres otro nombre de base
-- de datos o de login, usa Buscar y Reemplazar en todo el archivo
-- para 'tickets_db' / 'tickets_app' antes de correrlo.
--
-- Ejecutar conectado a la instancia de SQL Server (con un login
-- administrador, ej. sa) desde SSMS (abrir el archivo, Execute/F5)
-- o sqlcmd. Es seguro de correr varias veces: si la base, el login
-- o las tablas ya existen, no se vuelven a crear.
--
-- Generado con: python deploy/mssql/generate_schema_sql.py
-- Ver deploy/mssql/README.md para mas detalles.
-- ============================================================

IF DB_ID('tickets_db') IS NULL
BEGIN
    CREATE DATABASE [tickets_db];
END
GO

IF NOT EXISTS (SELECT * FROM sys.sql_logins WHERE name = 'tickets_app')
BEGIN
    CREATE LOGIN [tickets_app] WITH PASSWORD = 'CAMBIA_ESTA_CONTRASENA_123!', CHECK_POLICY = ON;
END
GO

USE [tickets_db];
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'tickets_app')
BEGIN
    CREATE USER [tickets_app] FOR LOGIN [tickets_app];
    ALTER ROLE db_owner ADD MEMBER [tickets_app];
END
GO

-- ==== Tablas (generadas desde las migraciones de Django) ====

-- ==== django_migrations (tabla de control interna de Django) ====
CREATE TABLE [django_migrations] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [app] nvarchar(255) NOT NULL, [name] nvarchar(255) NOT NULL, [applied] datetimeoffset NOT NULL);

-- ==== contenttypes.0001_initial ====
BEGIN TRANSACTION
--
-- Create model ContentType
--
CREATE TABLE [django_content_type] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [name] nvarchar(100) NOT NULL, [app_label] nvarchar(100) NOT NULL, [model] nvarchar(100) NOT NULL);
--
-- Alter unique_together for contenttype (1 constraint(s))
--
CREATE UNIQUE INDEX [django_content_type_app_label_model_76bd3d3b_uniq] ON [django_content_type] ([app_label], [model]) WHERE [app_label] IS NOT NULL AND [model] IS NOT NULL;
COMMIT;

-- ==== contenttypes.0002_remove_content_type_name ====
BEGIN TRANSACTION
--
-- Change Meta options on contenttype
--
-- (no-op)
--
-- Alter field name on contenttype
--
ALTER TABLE [django_content_type] ALTER COLUMN [name] nvarchar(100) NULL;
--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
--
-- Remove field name from contenttype
--
DECLARE @sql_dropidx_1 nvarchar(max) = '';
SELECT @sql_dropidx_1 = @sql_dropidx_1 + 'DROP INDEX [' + i.name + '] ON [django_content_type];' FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('django_content_type') AND c.name = 'name' AND i.is_primary_key = 0 AND i.type > 0;
IF @sql_dropidx_1 <> '' EXEC(@sql_dropidx_1);
ALTER TABLE [django_content_type] DROP COLUMN [name];
COMMIT;

-- ==== auth.0001_initial ====
BEGIN TRANSACTION
--
-- Create model Permission
--
CREATE TABLE [auth_permission] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [name] nvarchar(50) NOT NULL, [content_type_id] int NOT NULL, [codename] nvarchar(100) NOT NULL);
--
-- Create model Group
--
CREATE TABLE [auth_group] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [name] nvarchar(80) NOT NULL UNIQUE);
CREATE TABLE [auth_group_permissions] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [group_id] int NOT NULL, [permission_id] int NOT NULL);
--
-- Create model User
--
-- (no-op)
CREATE INDEX [auth_group_permissions_permission_id_84c5c92e] ON [auth_group_permissions] ([permission_id]);
CREATE UNIQUE INDEX [auth_group_permissions_group_id_permission_id_0cd325b0_uniq] ON [auth_group_permissions] ([group_id], [permission_id]) WHERE [group_id] IS NOT NULL AND [permission_id] IS NOT NULL;
ALTER TABLE [auth_permission] ADD CONSTRAINT [auth_permission_content_type_id_2f476e4b_fk_django_content_type_id] FOREIGN KEY ([content_type_id]) REFERENCES [django_content_type] ([id]);
CREATE INDEX [auth_permission_content_type_id_2f476e4b] ON [auth_permission] ([content_type_id]);
ALTER TABLE [auth_group_permissions] ADD CONSTRAINT [auth_group_permissions_permission_id_84c5c92e_fk_auth_permission_id] FOREIGN KEY ([permission_id]) REFERENCES [auth_permission] ([id]);
CREATE UNIQUE INDEX [auth_permission_content_type_id_codename_01ab375a_uniq] ON [auth_permission] ([content_type_id], [codename]) WHERE [content_type_id] IS NOT NULL AND [codename] IS NOT NULL;
CREATE INDEX [auth_group_permissions_group_id_b120cbf9] ON [auth_group_permissions] ([group_id]);
ALTER TABLE [auth_group_permissions] ADD CONSTRAINT [auth_group_permissions_group_id_b120cbf9_fk_auth_group_id] FOREIGN KEY ([group_id]) REFERENCES [auth_group] ([id]);
COMMIT;

-- ==== auth.0002_alter_permission_name_max_length ====
BEGIN TRANSACTION
--
-- Alter field name on permission
--
ALTER TABLE [auth_permission] ALTER COLUMN [name] nvarchar(255) NOT NULL;
COMMIT;

-- ==== auth.0003_alter_user_email_max_length ====
BEGIN TRANSACTION
--
-- Alter field email on user
--
-- (no-op)
COMMIT;

-- ==== auth.0004_alter_user_username_opts ====
BEGIN TRANSACTION
--
-- Alter field username on user
--
-- (no-op)
COMMIT;

-- ==== auth.0005_alter_user_last_login_null ====
BEGIN TRANSACTION
--
-- Alter field last_login on user
--
-- (no-op)
COMMIT;

-- ==== auth.0006_require_contenttypes_0002 ====

-- ==== auth.0007_alter_validators_add_error_messages ====
BEGIN TRANSACTION
--
-- Alter field username on user
--
-- (no-op)
COMMIT;

-- ==== auth.0008_alter_user_username_max_length ====
BEGIN TRANSACTION
--
-- Alter field username on user
--
-- (no-op)
COMMIT;

-- ==== auth.0009_alter_user_last_name_max_length ====
BEGIN TRANSACTION
--
-- Alter field last_name on user
--
-- (no-op)
COMMIT;

-- ==== auth.0010_alter_group_name_max_length ====
BEGIN TRANSACTION
--
-- Alter field name on group
--
ALTER TABLE [auth_group] DROP CONSTRAINT IF EXISTS [auth_group_name_a6ea08ec_uniq];
ALTER TABLE [auth_group] ALTER COLUMN [name] nvarchar(150) NOT NULL;
ALTER TABLE [auth_group] ADD CONSTRAINT [auth_group_name_a6ea08ec_uniq] UNIQUE ([name]);
COMMIT;

-- ==== auth.0011_update_proxy_permissions ====
BEGIN TRANSACTION
--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
COMMIT;

-- ==== auth.0012_alter_user_first_name_max_length ====
BEGIN TRANSACTION
--
-- Alter field first_name on user
--
-- (no-op)
COMMIT;

-- ==== tickets.0001_initial ====
BEGIN TRANSACTION
--
-- Create model Usuario
--
CREATE TABLE [tickets_usuario] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [password] nvarchar(128) NOT NULL, [last_login] datetimeoffset NULL, [is_superuser] bit NOT NULL, [username] nvarchar(150) NOT NULL UNIQUE, [first_name] nvarchar(150) NOT NULL, [last_name] nvarchar(150) NOT NULL, [email] nvarchar(254) NOT NULL, [is_staff] bit NOT NULL, [is_active] bit NOT NULL, [date_joined] datetimeoffset NOT NULL, [rol] nvarchar(10) NOT NULL);
CREATE TABLE [tickets_usuario_groups] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [usuario_id] bigint NOT NULL, [group_id] int NOT NULL);
CREATE TABLE [tickets_usuario_user_permissions] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [usuario_id] bigint NOT NULL, [permission_id] int NOT NULL);
ALTER TABLE [tickets_usuario_groups] ADD CONSTRAINT [tickets_usuario_groups_usuario_id_9c46a480_fk_tickets_usuario_id] FOREIGN KEY ([usuario_id]) REFERENCES [tickets_usuario] ([id]);
CREATE INDEX [tickets_usuario_user_permissions_usuario_id_1cb978c2] ON [tickets_usuario_user_permissions] ([usuario_id]);
ALTER TABLE [tickets_usuario_user_permissions] ADD CONSTRAINT [tickets_usuario_user_permissions_permission_id_6e9c6dd3_fk_auth_permission_id] FOREIGN KEY ([permission_id]) REFERENCES [auth_permission] ([id]);
CREATE UNIQUE INDEX [tickets_usuario_user_permissions_usuario_id_permission_id_c388dded_uniq] ON [tickets_usuario_user_permissions] ([usuario_id], [permission_id]) WHERE [usuario_id] IS NOT NULL AND [permission_id] IS NOT NULL;
ALTER TABLE [tickets_usuario_user_permissions] ADD CONSTRAINT [tickets_usuario_user_permissions_usuario_id_1cb978c2_fk_tickets_usuario_id] FOREIGN KEY ([usuario_id]) REFERENCES [tickets_usuario] ([id]);
CREATE INDEX [tickets_usuario_groups_usuario_id_9c46a480] ON [tickets_usuario_groups] ([usuario_id]);
ALTER TABLE [tickets_usuario_groups] ADD CONSTRAINT [tickets_usuario_groups_group_id_b1f24160_fk_auth_group_id] FOREIGN KEY ([group_id]) REFERENCES [auth_group] ([id]);
CREATE UNIQUE INDEX [tickets_usuario_groups_usuario_id_group_id_dcc19ad1_uniq] ON [tickets_usuario_groups] ([usuario_id], [group_id]) WHERE [usuario_id] IS NOT NULL AND [group_id] IS NOT NULL;
CREATE INDEX [tickets_usuario_user_permissions_permission_id_6e9c6dd3] ON [tickets_usuario_user_permissions] ([permission_id]);
CREATE INDEX [tickets_usuario_groups_group_id_b1f24160] ON [tickets_usuario_groups] ([group_id]);
COMMIT;

-- ==== admin.0001_initial ====
BEGIN TRANSACTION
--
-- Create model LogEntry
--
CREATE TABLE [django_admin_log] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [action_time] datetimeoffset NOT NULL, [object_id] nvarchar(max) NULL, [object_repr] nvarchar(200) NOT NULL, [action_flag] smallint NOT NULL CONSTRAINT django_admin_log_action_flag_a8637d59_check CHECK ([action_flag] >= 0), [change_message] nvarchar(max) NOT NULL, [content_type_id] int NULL, [user_id] bigint NOT NULL);
ALTER TABLE [django_admin_log] ADD CONSTRAINT [django_admin_log_content_type_id_c4bce8eb_fk_django_content_type_id] FOREIGN KEY ([content_type_id]) REFERENCES [django_content_type] ([id]);
ALTER TABLE [django_admin_log] ADD CONSTRAINT [django_admin_log_user_id_c564eba6_fk_tickets_usuario_id] FOREIGN KEY ([user_id]) REFERENCES [tickets_usuario] ([id]);
CREATE INDEX [django_admin_log_user_id_c564eba6] ON [django_admin_log] ([user_id]);
CREATE INDEX [django_admin_log_content_type_id_c4bce8eb] ON [django_admin_log] ([content_type_id]);
COMMIT;

-- ==== admin.0002_logentry_remove_auto_add ====
BEGIN TRANSACTION
--
-- Alter field action_time on logentry
--
-- (no-op)
COMMIT;

-- ==== admin.0003_logentry_add_action_flag_choices ====
BEGIN TRANSACTION
--
-- Alter field action_flag on logentry
--
-- (no-op)
COMMIT;

-- ==== axes.0001_initial ====
BEGIN TRANSACTION
--
-- Create model AccessAttempt
--
CREATE TABLE [axes_accessattempt] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [user_agent] nvarchar(255) NOT NULL, [ip_address] nvarchar(39) NULL, [username] nvarchar(255) NULL, [trusted] bit NOT NULL, [http_accept] nvarchar(1025) NOT NULL, [path_info] nvarchar(255) NOT NULL, [attempt_time] datetimeoffset NOT NULL, [get_data] nvarchar(max) NOT NULL, [post_data] nvarchar(max) NOT NULL, [failures_since_start] int NOT NULL CONSTRAINT axes_accessattempt_failures_since_start_7154a700_check CHECK ([failures_since_start] >= 0));
--
-- Create model AccessLog
--
CREATE TABLE [axes_accesslog] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [user_agent] nvarchar(255) NOT NULL, [ip_address] nvarchar(39) NULL, [username] nvarchar(255) NULL, [trusted] bit NOT NULL, [http_accept] nvarchar(1025) NOT NULL, [path_info] nvarchar(255) NOT NULL, [attempt_time] datetimeoffset NOT NULL, [logout_time] datetimeoffset NULL);
COMMIT;

-- ==== axes.0002_auto_20151217_2044 ====
BEGIN TRANSACTION
--
-- Alter field ip_address on accessattempt
--
CREATE INDEX [axes_accessattempt_ip_address_10922d9c] ON [axes_accessattempt] ([ip_address]);
--
-- Alter field trusted on accessattempt
--
CREATE INDEX [axes_accessattempt_trusted_0eddf52e] ON [axes_accessattempt] ([trusted]);
--
-- Alter field user_agent on accessattempt
--
CREATE INDEX [axes_accessattempt_user_agent_ad89678b] ON [axes_accessattempt] ([user_agent]);
--
-- Alter field username on accessattempt
--
CREATE INDEX [axes_accessattempt_username_3f2d4ca0] ON [axes_accessattempt] ([username]);
--
-- Alter field ip_address on accesslog
--
CREATE INDEX [axes_accesslog_ip_address_86b417e5] ON [axes_accesslog] ([ip_address]);
--
-- Alter field trusted on accesslog
--
CREATE INDEX [axes_accesslog_trusted_496c5681] ON [axes_accesslog] ([trusted]);
--
-- Alter field user_agent on accesslog
--
CREATE INDEX [axes_accesslog_user_agent_0e659004] ON [axes_accesslog] ([user_agent]);
--
-- Alter field username on accesslog
--
CREATE INDEX [axes_accesslog_username_df93064b] ON [axes_accesslog] ([username]);
COMMIT;

-- ==== axes.0003_auto_20160322_0929 ====
BEGIN TRANSACTION
--
-- Alter field failures_since_start on accessattempt
--
-- (no-op)
--
-- Alter field get_data on accessattempt
--
-- (no-op)
--
-- Alter field http_accept on accessattempt
--
-- (no-op)
--
-- Alter field ip_address on accessattempt
--
-- (no-op)
--
-- Alter field path_info on accessattempt
--
-- (no-op)
--
-- Alter field post_data on accessattempt
--
-- (no-op)
--
-- Alter field http_accept on accesslog
--
-- (no-op)
--
-- Alter field ip_address on accesslog
--
-- (no-op)
--
-- Alter field path_info on accesslog
--
-- (no-op)
COMMIT;

-- ==== axes.0004_auto_20181024_1538 ====
BEGIN TRANSACTION
--
-- Change Meta options on accessattempt
--
-- (no-op)
--
-- Change Meta options on accesslog
--
-- (no-op)
--
-- Alter field attempt_time on accessattempt
--
-- (no-op)
--
-- Alter field user_agent on accessattempt
--
-- (no-op)
--
-- Alter field username on accessattempt
--
-- (no-op)
--
-- Alter field attempt_time on accesslog
--
-- (no-op)
--
-- Alter field logout_time on accesslog
--
-- (no-op)
--
-- Alter field user_agent on accesslog
--
-- (no-op)
--
-- Alter field username on accesslog
--
-- (no-op)
COMMIT;

-- ==== axes.0005_remove_accessattempt_trusted ====
BEGIN TRANSACTION
--
-- Remove field trusted from accessattempt
--
DECLARE @sql_dropidx_2 nvarchar(max) = '';
SELECT @sql_dropidx_2 = @sql_dropidx_2 + 'DROP INDEX [' + i.name + '] ON [axes_accessattempt];' FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('axes_accessattempt') AND c.name = 'trusted' AND i.is_primary_key = 0 AND i.type > 0;
IF @sql_dropidx_2 <> '' EXEC(@sql_dropidx_2);
ALTER TABLE [axes_accessattempt] DROP COLUMN [trusted];
COMMIT;

-- ==== axes.0006_remove_accesslog_trusted ====
BEGIN TRANSACTION
--
-- Remove field trusted from accesslog
--
DECLARE @sql_dropidx_3 nvarchar(max) = '';
SELECT @sql_dropidx_3 = @sql_dropidx_3 + 'DROP INDEX [' + i.name + '] ON [axes_accesslog];' FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('axes_accesslog') AND c.name = 'trusted' AND i.is_primary_key = 0 AND i.type > 0;
IF @sql_dropidx_3 <> '' EXEC(@sql_dropidx_3);
ALTER TABLE [axes_accesslog] DROP COLUMN [trusted];
COMMIT;

-- ==== axes.0007_alter_accessattempt_unique_together ====
BEGIN TRANSACTION
--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
--
-- Alter unique_together for accessattempt (1 constraint(s))
--
CREATE UNIQUE INDEX [axes_accessattempt_username_ip_address_user_agent_8ea22282_uniq] ON [axes_accessattempt] ([username], [ip_address], [user_agent]) WHERE [username] IS NOT NULL AND [ip_address] IS NOT NULL AND [user_agent] IS NOT NULL;
COMMIT;

-- ==== axes.0008_accessfailurelog ====
BEGIN TRANSACTION
--
-- Create model AccessFailureLog
--
CREATE TABLE [axes_accessfailurelog] ([id] int NOT NULL PRIMARY KEY IDENTITY (1, 1), [user_agent] nvarchar(255) NOT NULL, [ip_address] nvarchar(39) NULL, [username] nvarchar(255) NULL, [http_accept] nvarchar(1025) NOT NULL, [path_info] nvarchar(255) NOT NULL, [attempt_time] datetimeoffset NOT NULL, [locked_out] bit NOT NULL);
CREATE INDEX [axes_accessfailurelog_ip_address_2e9f5a7f] ON [axes_accessfailurelog] ([ip_address]);
CREATE INDEX [axes_accessfailurelog_username_a8b7e8a4] ON [axes_accessfailurelog] ([username]);
CREATE INDEX [axes_accessfailurelog_user_agent_ea145dda] ON [axes_accessfailurelog] ([user_agent]);
COMMIT;

-- ==== axes.0009_add_session_hash ====
BEGIN TRANSACTION
--
-- Add field session_hash to accesslog
--
ALTER TABLE [axes_accesslog] ADD [session_hash] nvarchar(64) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'axes_accesslog' AND c.name = 'session_hash';
ALTER TABLE [axes_accesslog] DROP CONSTRAINT IF EXISTS [session_hash];
COMMIT;

-- ==== axes.0010_accessattemptexpiration ====
BEGIN TRANSACTION
--
-- Create model AccessAttemptExpiration
--
CREATE TABLE [axes_accessattemptexpiration] ([access_attempt_id] int NOT NULL PRIMARY KEY, [expires_at] datetimeoffset NOT NULL);
ALTER TABLE [axes_accessattemptexpiration] ADD CONSTRAINT [axes_accessattemptexpiration_access_attempt_id_6b73a47a_fk_axes_accessattempt_id] FOREIGN KEY ([access_attempt_id]) REFERENCES [axes_accessattempt] ([id]);
COMMIT;

-- ==== sessions.0001_initial ====
BEGIN TRANSACTION
--
-- Create model Session
--
CREATE TABLE [django_session] ([session_key] nvarchar(40) NOT NULL PRIMARY KEY, [session_data] nvarchar(max) NOT NULL, [expire_date] datetimeoffset NOT NULL);
CREATE INDEX [django_session_expire_date_a5c62663] ON [django_session] ([expire_date]);
COMMIT;

-- ==== tickets.0002_empresa_usuario_empresas ====
BEGIN TRANSACTION
--
-- Create model Empresa
--
CREATE TABLE [tickets_empresa] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [nombre] nvarchar(150) NOT NULL UNIQUE, [descripcion] nvarchar(255) NOT NULL, [activa] bit NOT NULL, [fecha_creacion] datetimeoffset NOT NULL);
--
-- Add field empresas to usuario
--
CREATE TABLE [tickets_usuario_empresas] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [usuario_id] bigint NOT NULL, [empresa_id] bigint NOT NULL);
ALTER TABLE [tickets_usuario_empresas] ADD CONSTRAINT [tickets_usuario_empresas_empresa_id_785c1ad9_fk_tickets_empresa_id] FOREIGN KEY ([empresa_id]) REFERENCES [tickets_empresa] ([id]);
CREATE INDEX [tickets_usuario_empresas_empresa_id_785c1ad9] ON [tickets_usuario_empresas] ([empresa_id]);
CREATE INDEX [tickets_usuario_empresas_usuario_id_ad589812] ON [tickets_usuario_empresas] ([usuario_id]);
ALTER TABLE [tickets_usuario_empresas] ADD CONSTRAINT [tickets_usuario_empresas_usuario_id_ad589812_fk_tickets_usuario_id] FOREIGN KEY ([usuario_id]) REFERENCES [tickets_usuario] ([id]);
CREATE UNIQUE INDEX [tickets_usuario_empresas_usuario_id_empresa_id_63501da9_uniq] ON [tickets_usuario_empresas] ([usuario_id], [empresa_id]) WHERE [usuario_id] IS NOT NULL AND [empresa_id] IS NOT NULL;
COMMIT;

-- ==== tickets.0003_ticket ====
BEGIN TRANSACTION
--
-- Create model Ticket
--
CREATE TABLE [tickets_ticket] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [tipo] nvarchar(15) NOT NULL, [titulo] nvarchar(150) NOT NULL, [descripcion] nvarchar(max) NOT NULL, [estado] nvarchar(15) NOT NULL, [fecha_creacion] datetimeoffset NOT NULL, [fecha_actualizacion] datetimeoffset NOT NULL, [cliente_id] bigint NOT NULL, [empresa_id] bigint NOT NULL);
ALTER TABLE [tickets_ticket] ADD CONSTRAINT [tickets_ticket_cliente_id_051f0dae_fk_tickets_usuario_id] FOREIGN KEY ([cliente_id]) REFERENCES [tickets_usuario] ([id]);
CREATE INDEX [tickets_ticket_empresa_id_2f938afb] ON [tickets_ticket] ([empresa_id]);
ALTER TABLE [tickets_ticket] ADD CONSTRAINT [tickets_ticket_empresa_id_2f938afb_fk_tickets_empresa_id] FOREIGN KEY ([empresa_id]) REFERENCES [tickets_empresa] ([id]);
CREATE INDEX [tickets_ticket_cliente_id_051f0dae] ON [tickets_ticket] ([cliente_id]);
COMMIT;

-- ==== tickets.0004_ticket_contacto_alternativo_ticket_dato_contacto_and_more ====
BEGIN TRANSACTION
--
-- Add field contacto_alternativo to ticket
--
ALTER TABLE [tickets_ticket] ADD [contacto_alternativo] nvarchar(150) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'contacto_alternativo';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [contacto_alternativo];
--
-- Add field dato_contacto to ticket
--
ALTER TABLE [tickets_ticket] ADD [dato_contacto] nvarchar(150) DEFAULT 'sin dato' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'dato_contacto';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [dato_contacto];
--
-- Add field medio_contacto to ticket
--
ALTER TABLE [tickets_ticket] ADD [medio_contacto] nvarchar(10) DEFAULT 'correo' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'medio_contacto';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [medio_contacto];
COMMIT;

-- ==== tickets.0005_alter_usuario_rol ====
BEGIN TRANSACTION
--
-- Alter field rol on usuario
--
-- (no-op)
COMMIT;

-- ==== tickets.0006_ticket_evidencia_resolucion ====
BEGIN TRANSACTION
--
-- Add field evidencia_resolucion to ticket
--
ALTER TABLE [tickets_ticket] ADD [evidencia_resolucion] nvarchar(max) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'evidencia_resolucion';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [evidencia_resolucion];
COMMIT;

-- ==== tickets.0007_ticketactualizacion ====
BEGIN TRANSACTION
--
-- Create model TicketActualizacion
--
CREATE TABLE [tickets_ticketactualizacion] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [estado_en_ese_momento] nvarchar(15) NOT NULL, [comentario] nvarchar(max) NOT NULL, [fecha_creacion] datetimeoffset NOT NULL, [autor_id] bigint NULL, [ticket_id] bigint NOT NULL);
ALTER TABLE [tickets_ticketactualizacion] ADD CONSTRAINT [tickets_ticketactualizacion_autor_id_0b3e4e46_fk_tickets_usuario_id] FOREIGN KEY ([autor_id]) REFERENCES [tickets_usuario] ([id]);
CREATE INDEX [tickets_ticketactualizacion_autor_id_0b3e4e46] ON [tickets_ticketactualizacion] ([autor_id]);
CREATE INDEX [tickets_ticketactualizacion_ticket_id_94ba2691] ON [tickets_ticketactualizacion] ([ticket_id]);
ALTER TABLE [tickets_ticketactualizacion] ADD CONSTRAINT [tickets_ticketactualizacion_ticket_id_94ba2691_fk_tickets_ticket_id] FOREIGN KEY ([ticket_id]) REFERENCES [tickets_ticket] ([id]);
COMMIT;

-- ==== tickets.0008_ticket_cerrado_por_ticket_fecha_cierre ====
BEGIN TRANSACTION
--
-- Add field cerrado_por to ticket
--
ALTER TABLE [tickets_ticket] ADD [cerrado_por_id] bigint NULL;
--
-- Add field fecha_cierre to ticket
--
ALTER TABLE [tickets_ticket] ADD [fecha_cierre] datetimeoffset NULL;
CREATE INDEX [tickets_ticket_cerrado_por_id_8d2e9cc4] ON [tickets_ticket] ([cerrado_por_id]);
ALTER TABLE [tickets_ticket] ADD CONSTRAINT [tickets_ticket_cerrado_por_id_8d2e9cc4_fk_tickets_usuario_id] FOREIGN KEY ([cerrado_por_id]) REFERENCES [tickets_usuario] ([id]);
COMMIT;

-- ==== tickets.0009_empresa_eliminada_empresa_fecha_eliminacion ====
BEGIN TRANSACTION
--
-- Add field eliminada to empresa
--
ALTER TABLE [tickets_empresa] ADD [eliminada] bit DEFAULT 0 NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_empresa' AND c.name = 'eliminada';
ALTER TABLE [tickets_empresa] DROP CONSTRAINT IF EXISTS [eliminada];
--
-- Add field fecha_eliminacion to empresa
--
ALTER TABLE [tickets_empresa] ADD [fecha_eliminacion] datetimeoffset NULL;
COMMIT;

-- ==== tickets.0010_ticket_requiere_atencion ====
BEGIN TRANSACTION
--
-- Add field requiere_atencion to ticket
--
ALTER TABLE [tickets_ticket] ADD [requiere_atencion] bit DEFAULT 0 NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'requiere_atencion';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [requiere_atencion];
COMMIT;

-- ==== tickets.0011_ticketimagen ====
BEGIN TRANSACTION
--
-- Create model TicketImagen
--
CREATE TABLE [tickets_ticketimagen] ([id] bigint NOT NULL PRIMARY KEY IDENTITY (1, 1), [imagen] nvarchar(100) NOT NULL, [fecha_creacion] datetimeoffset NOT NULL, [actualizacion_id] bigint NULL, [ticket_id] bigint NULL);
ALTER TABLE [tickets_ticketimagen] ADD CONSTRAINT [tickets_ticketimagen_actualizacion_id_f7563e89_fk_tickets_ticketactualizacion_id] FOREIGN KEY ([actualizacion_id]) REFERENCES [tickets_ticketactualizacion] ([id]);
CREATE INDEX [tickets_ticketimagen_ticket_id_e4766c14] ON [tickets_ticketimagen] ([ticket_id]);
ALTER TABLE [tickets_ticketimagen] ADD CONSTRAINT [tickets_ticketimagen_ticket_id_e4766c14_fk_tickets_ticket_id] FOREIGN KEY ([ticket_id]) REFERENCES [tickets_ticket] ([id]);
CREATE INDEX [tickets_ticketimagen_actualizacion_id_f7563e89] ON [tickets_ticketimagen] ([actualizacion_id]);
COMMIT;

-- ==== tickets.0012_ticket_fecha_limite_confirmacion_and_more ====
BEGIN TRANSACTION
--
-- Add field fecha_limite_confirmacion to ticket
--
ALTER TABLE [tickets_ticket] ADD [fecha_limite_confirmacion] datetimeoffset NULL;
--
-- Add field motivo_cierre to ticket
--
ALTER TABLE [tickets_ticket] ADD [motivo_cierre] nvarchar(12) NULL;
--
-- Add field pdf_cierre to ticket
--
ALTER TABLE [tickets_ticket] ADD [pdf_cierre] nvarchar(100) NULL;
--
-- Alter field estado on ticket
--
ALTER TABLE [tickets_ticket] ALTER COLUMN [estado] nvarchar(25) NOT NULL;
--
-- Alter field estado_en_ese_momento on ticketactualizacion
--
ALTER TABLE [tickets_ticketactualizacion] ALTER COLUMN [estado_en_ese_momento] nvarchar(25) NOT NULL;
COMMIT;

-- ==== tickets.0013_alter_usuario_rol ====
BEGIN TRANSACTION
--
-- Alter field rol on usuario
--
-- (no-op)
COMMIT;

-- ==== tickets.0014_usuario_telefono_alter_usuario_email ====
BEGIN TRANSACTION
--
-- Add field telefono to usuario
--
ALTER TABLE [tickets_usuario] ADD [telefono] nvarchar(20) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_usuario' AND c.name = 'telefono';
ALTER TABLE [tickets_usuario] DROP CONSTRAINT IF EXISTS [telefono];
--
-- Alter field email on usuario
--
-- (no-op)
COMMIT;

-- ==== tickets.0015_alter_usuario_rol ====
BEGIN TRANSACTION
--
-- Alter field rol on usuario
--
-- (no-op)
COMMIT;

-- ==== tickets.0016_ticket_cliente_eliminado_nombre_alter_ticket_cliente_and_more ====
BEGIN TRANSACTION
--
-- Add field cliente_eliminado_nombre to ticket
--
ALTER TABLE [tickets_ticket] ADD [cliente_eliminado_nombre] nvarchar(150) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'cliente_eliminado_nombre';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [cliente_eliminado_nombre];
--
-- Alter field cliente on ticket
--
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [tickets_ticket_cliente_id_051f0dae_fk_tickets_usuario_id];
DROP INDEX [tickets_ticket_cliente_id_051f0dae] ON [tickets_ticket];
ALTER TABLE [tickets_ticket] ALTER COLUMN [cliente_id] bigint NULL;
CREATE INDEX [tickets_ticket_cliente_id_051f0dae] ON [tickets_ticket] ([cliente_id]);
ALTER TABLE [tickets_ticket] ADD CONSTRAINT [tickets_ticket_cliente_id_051f0dae_fk_tickets_usuario_id] FOREIGN KEY ([cliente_id]) REFERENCES [tickets_usuario] ([id]);
--
-- Alter field motivo_cierre on ticket
--
ALTER TABLE [tickets_ticket] ALTER COLUMN [motivo_cierre] nvarchar(20) NULL;
COMMIT;

-- ==== tickets.0017_usuario_protegido ====
BEGIN TRANSACTION
--
-- Add field protegido to usuario
--
ALTER TABLE [tickets_usuario] ADD [protegido] bit DEFAULT 0 NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_usuario' AND c.name = 'protegido';
ALTER TABLE [tickets_usuario] DROP CONSTRAINT IF EXISTS [protegido];
COMMIT;

-- ==== tickets.0018_alter_ticketimagen_imagen ====
BEGIN TRANSACTION
--
-- Alter field imagen on ticketimagen
--
-- (no-op)
COMMIT;

-- ==== tickets.0019_ticketimagen_nombre_original_and_more ====
BEGIN TRANSACTION
--
-- Add field nombre_original to ticketimagen
--
ALTER TABLE [tickets_ticketimagen] ADD [nombre_original] nvarchar(255) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticketimagen' AND c.name = 'nombre_original';
ALTER TABLE [tickets_ticketimagen] DROP CONSTRAINT IF EXISTS [nombre_original];
--
-- Alter field imagen on ticketimagen
--
-- (no-op)
COMMIT;

-- ==== tickets.0020_alter_ticketimagen_imagen ====
BEGIN TRANSACTION
--
-- Alter field imagen on ticketimagen
--
-- (no-op)
COMMIT;

-- ==== tickets.0021_ticket_requiere_atencion_cliente ====
BEGIN TRANSACTION
--
-- Add field requiere_atencion_cliente to ticket
--
ALTER TABLE [tickets_ticket] ADD [requiere_atencion_cliente] bit DEFAULT 0 NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'requiere_atencion_cliente';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [requiere_atencion_cliente];
COMMIT;

-- ==== tickets.0022_empresa_logo ====
BEGIN TRANSACTION
--
-- Add field logo to empresa
--
ALTER TABLE [tickets_empresa] ADD [logo] nvarchar(100) NULL;
COMMIT;

-- ==== tickets.0023_ticket_empresa_eliminada_nombre_alter_ticket_empresa_and_more ====
BEGIN TRANSACTION
--
-- Add field empresa_eliminada_nombre to ticket
--
ALTER TABLE [tickets_ticket] ADD [empresa_eliminada_nombre] nvarchar(150) DEFAULT '' NOT NULL;
SELECT d.name FROM sys.default_constraints d INNER JOIN sys.tables t ON d.parent_object_id = t.object_id INNER JOIN sys.columns c ON d.parent_object_id = c.object_id AND d.parent_column_id = c.column_id INNER JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE t.name = 'tickets_ticket' AND c.name = 'empresa_eliminada_nombre';
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [empresa_eliminada_nombre];
--
-- Alter field empresa on ticket
--
ALTER TABLE [tickets_ticket] DROP CONSTRAINT IF EXISTS [tickets_ticket_empresa_id_2f938afb_fk_tickets_empresa_id];
DROP INDEX [tickets_ticket_empresa_id_2f938afb] ON [tickets_ticket];
ALTER TABLE [tickets_ticket] ALTER COLUMN [empresa_id] bigint NULL;
CREATE INDEX [tickets_ticket_empresa_id_2f938afb] ON [tickets_ticket] ([empresa_id]);
ALTER TABLE [tickets_ticket] ADD CONSTRAINT [tickets_ticket_empresa_id_2f938afb_fk_tickets_empresa_id] FOREIGN KEY ([empresa_id]) REFERENCES [tickets_empresa] ([id]);
--
-- Alter field motivo_cierre on ticket
--
-- (no-op)
COMMIT;

-- ==== Registro de migraciones aplicadas (para que Django reconozca el esquema) ====
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('contenttypes', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('contenttypes', '0002_remove_content_type_name', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0002_alter_permission_name_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0003_alter_user_email_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0004_alter_user_username_opts', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0005_alter_user_last_login_null', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0006_require_contenttypes_0002', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0007_alter_validators_add_error_messages', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0008_alter_user_username_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0009_alter_user_last_name_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0010_alter_group_name_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0011_update_proxy_permissions', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('auth', '0012_alter_user_first_name_max_length', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('admin', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('admin', '0002_logentry_remove_auto_add', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('admin', '0003_logentry_add_action_flag_choices', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0002_auto_20151217_2044', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0003_auto_20160322_0929', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0004_auto_20181024_1538', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0005_remove_accessattempt_trusted', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0006_remove_accesslog_trusted', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0007_alter_accessattempt_unique_together', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0008_accessfailurelog', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0009_add_session_hash', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('axes', '0010_accessattemptexpiration', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('sessions', '0001_initial', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0002_empresa_usuario_empresas', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0003_ticket', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0004_ticket_contacto_alternativo_ticket_dato_contacto_and_more', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0005_alter_usuario_rol', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0006_ticket_evidencia_resolucion', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0007_ticketactualizacion', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0008_ticket_cerrado_por_ticket_fecha_cierre', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0009_empresa_eliminada_empresa_fecha_eliminacion', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0010_ticket_requiere_atencion', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0011_ticketimagen', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0012_ticket_fecha_limite_confirmacion_and_more', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0013_alter_usuario_rol', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0014_usuario_telefono_alter_usuario_email', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0015_alter_usuario_rol', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0016_ticket_cliente_eliminado_nombre_alter_ticket_cliente_and_more', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0017_usuario_protegido', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0018_alter_ticketimagen_imagen', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0019_ticketimagen_nombre_original_and_more', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0020_alter_ticketimagen_imagen', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0021_ticket_requiere_atencion_cliente', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0022_empresa_logo', '2026-07-15 03:22:06');
INSERT INTO [django_migrations] ([app], [name], [applied]) VALUES ('tickets', '0023_ticket_empresa_eliminada_nombre_alter_ticket_empresa_and_more', '2026-07-15 03:22:06');
