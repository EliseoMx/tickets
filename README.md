# Sistema de Tickets — INCAP

Sistema interno de atención a clientes (soporte técnico) multi-empresa, hecho en Django. Permite que los clientes de varias empresas levanten incidentes o requerimientos, que un equipo de soporte los atienda, y que el cierre quede documentado y notificado por correo.

## ¿Qué hace el sistema?

- Cada **empresa** (cliente de INCAP) tiene sus propios usuarios y tickets, aislados del resto.
- Los **clientes** levantan tickets (incidente o requerimiento), opcionalmente con imágenes de evidencia.
- El equipo de **soporte** los atiende desde una bandeja, agrega actualizaciones y, al resolverlos, el ticket pasa a **pendiente de confirmación** en vez de cerrarse de inmediato.
- El cliente confirma que quedó resuelto (o indica que no), y si no responde en 3 días el ticket se cierra solo.
- Al cerrarse (por confirmación o automático), se genera un **PDF con el historial completo** (incluye las imágenes antes de borrarlas), se manda un **correo de cierre**, y se liberan las imágenes de la nube.
- Todas las tablas del sistema (tickets, usuarios, empresas) tienen **filtros por columna** y se pueden **exportar a CSV o Excel**.

## Roles y permisos

| Rol | Puede |
|---|---|
| **Super admin** | Ver y editar todo, sin restricciones, en todas las empresas (incluidas las que se creen después). Puede crear otros administradores y eliminar usuarios permanentemente |
| **Agente de Soporte** | Ver y atender todos los tickets de sus empresas asignadas (bandeja, actualizaciones, cierres) |
| **Agente Cliente** | Levantar tickets, crear usuarios clientes de su empresa, activarlos/desactivarlos, restablecerles la contraseña, y ver (solo lectura) los tickets de todos los usuarios de su empresa |
| **Cliente** | Levantar tickets y ver/comentar únicamente los suyos |

El login acepta usuario **o correo electrónico**. El campo "Rol" al crear un usuario incluye la opción
**Administrador** (visible solo para un super admin), que da acceso total sin necesidad de asignar empresas.

Además existe una **cuenta de administrador protegida**: se crea sola después de cada `migrate` (si no
existe todavía) con los datos del `.env`, y no se puede editar, desactivar ni eliminar desde la interfaz
(ni siquiera por otro superadmin) — sirve como respaldo de acceso permanente al sistema. Ver la sección
de Configuración.

## Flujo habitual de un ticket

```mermaid
flowchart TD
    A[Cliente levanta ticket<br/>Incidente o Requerimiento] --> B[Ticket: Abierto]
    B --> C[Soporte lo atiende<br/>agrega actualizaciones]
    C --> D{Soporte marca<br/>estado}
    D -->|En proceso| C
    D -->|Cerrado| E[Ticket: Pendiente de confirmación<br/>límite 3 días]
    E --> F{Cliente responde?}
    F -->|Confirma cierre| G[Cierre definitivo]
    F -->|Aún no resuelto| C
    F -->|No responde en 3 días| G
    G --> H[Genera PDF con historial e imágenes]
    H --> I[Envía correo de cierre<br/>cliente + agente, CC/BCC configurables]
    I --> J[Elimina imágenes de Cloudinary]
    J --> K[Ticket: Cerrado]
    K -.->|Soporte puede reabrir| C
```

## Funcionalidades importantes

- **Imágenes en tickets**: hasta 3 por envío, 5MB cada una, almacenadas en **Cloudinary** (no en el servidor).
- **Cierre con confirmación del cliente**: nunca se cierra un ticket de forma directa al marcarlo "Cerrado"; siempre pasa por la etapa de confirmación. El auto-cierre por vencimiento se revisa cada vez que soporte carga la bandeja de tickets (no es un cron real).
- **PDF de cierre**: se genera con `reportlab`, se guarda en Cloudinary (almacenamiento tipo *raw*), y se adjunta directo en el correo (no se expone ningún link público desde la app).
- **Correo de cierre**: vía Gmail SMTP. Va al cliente y al agente que atendió; en copia el contacto alternativo si es un correo válido; en copia oculta siempre la dirección configurada en `EMAIL_BCC_CIERRE`.
- **Filtros y exportación**: cada tabla tiene una fila de filtros (uno por columna, con los valores reales encontrados) más un buscador general. Los botones de exportar (CSV/Excel) exportan exactamente lo que está filtrado/visible en pantalla, no la tabla completa. El Excel es un `.xlsx` real, generado en el navegador sin dependencias externas.
- **Zona horaria**: la base de datos guarda todo en UTC. Un middleware (`tickets/middleware.py`) detecta la zona horaria del navegador de cada visitante (vía cookie) y localiza automáticamente todas las fechas mostradas y exportadas — sin tocar cómo se almacenan.
- **Reloj y versión del sistema**: en el header de cada pantalla se muestra la hora en vivo con su zona horaria, y debajo la versión del sistema (`v<commits> (<hash>)`), calculada automáticamente desde el historial de git — avanza sola con cada commit/merge.
- **Borrado de empresas**: es un soft-delete (se marca `eliminada=True` y se renombra con fecha), nunca se borra de verdad para conservar el historial de tickets.
- **Empresas nuevas**: al crearse, se vinculan automáticamente a todos los administradores existentes.
- **Página de ayuda**: dentro del sistema, con explicación de roles y del flujo de un ticket para cualquier usuario.

## Gestión de usuarios y contraseñas

- **Alta de usuarios**: individual o por **carga masiva** (CSV con plantilla descargable). En ambos casos se genera un **PIN numérico de 4 dígitos** como contraseña y se manda un **correo de bienvenida** con los datos de acceso — el PIN nunca se muestra en pantalla ni en el CSV de resultado, solo llega por correo.
- **Restablecer contraseña**: un Agente Cliente o el administrador puede generarle un PIN nuevo a otro usuario; se le avisa por correo, sin exponerlo en pantalla.
- **Cambiar mi contraseña**: cualquier usuario logueado puede cambiar su propia contraseña desde el botón junto a "Cerrar sesión". Pide la contraseña actual, valida que la nueva sea de 4 números, avisa por correo, y no cierra la sesión.
- **Activar / desactivar**: soft-delete de usuarios — bloquea el login sin borrar su historial de tickets; reversible en cualquier momento.
- **Eliminar permanentemente** (solo super admin): borra la cuenta de verdad. Sus tickets **nunca se borran**: los que sigan abiertos se cierran automáticamente (motivo "Cerrado por eliminación de usuario", con su correo de cierre normal) y se conserva el nombre de usuario en el historial aunque la cuenta ya no exista. Un ticket sin cliente ya no se puede reabrir.

## Seguridad

- **Bloqueo por fuerza bruta** (`django-axes`): las contraseñas son un PIN de 4 dígitos (10,000 combinaciones), así que el login se bloquea tras 5 intentos fallidos por combinación usuario+IP, con 15 minutos de enfriamiento. Se puede desbloquear manualmente con `python manage.py axes_reset`.
- **Prevención de doble envío**: un script compartido (`_prevenir_doble_envio.html`) deshabilita el botón de cualquier formulario apenas se envía, para evitar duplicados por doble clic o conexión lenta. Respeta los diálogos de confirmación existentes (si se cancela, el botón no se deshabilita).
- **Nunca se muestran contraseñas en pantalla**: los PIN (de bienvenida, restablecimiento o cambio propio) solo se envían por correo, nunca aparecen en la interfaz ni en los CSV de resultado.

## Textos y marca configurables

Estas variables son opcionales (si no se definen, se usan los valores entre paréntesis):

- `NOMBRE_SISTEMA` (`Atención al Cliente INCAP`): nombre mostrado en el header de todas las pantallas, en los títulos de pestaña y en los correos.
- `TEXTO_SELECCION_EMPRESA` (`Selecciona una empresa`): texto del encabezado en la pantalla de inicio.

## Stack

- **Backend**: Django 5.2, SQLite (desarrollo).
- **Imágenes y PDFs**: Cloudinary (`django-cloudinary-storage`).
- **Correo**: SMTP (Gmail).
- **Seguridad**: `django-axes` (bloqueo de login).
- **Frontend**: HTML/CSS/JS simple por plantilla, sin frameworks ni build step.

## Configuración

1. `pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y completar:
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
   - `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (contraseña de aplicación de Gmail)
   - `EMAIL_BCC_CIERRE` (correo que siempre recibe copia oculta al cerrar un ticket)
   - `ADMIN_PROTEGIDO_USERNAME`, `ADMIN_PROTEGIDO_EMAIL`, `ADMIN_PROTEGIDO_TELEFONO`, `ADMIN_PROTEGIDO_PASSWORD`
     (opcional pero recomendado: datos de la cuenta protegida que se crea sola; nunca subir estos valores a git)
   - `NOMBRE_SISTEMA`, `TEXTO_SELECCION_EMPRESA` (opcional, ver sección de textos configurables)
3. `python manage.py migrate`
4. `python manage.py runserver`
