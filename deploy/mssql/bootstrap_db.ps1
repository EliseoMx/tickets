<#
.SYNOPSIS
    Crea la base de datos y el login de SQL Server para el proyecto (si no existen
    todavia) y opcionalmente corre las migraciones de Django. Seguro de correr
    varias veces: no falla si la base, el login o el usuario ya existen.

.PARAMETER SqlInstance
    Servidor/instancia de SQL Server. Por default "localhost\SQLEXPRESS".

.PARAMETER SaPassword
    Contrasena del login administrador (normalmente "sa") que ya exista en el
    servidor. Se usa solo para crear la base y el login nuevo, no se guarda.

.PARAMETER DbName
    Nombre de la base de datos a crear. Por default "tickets_db".

.PARAMETER AppLogin
    Login/usuario que va a usar la aplicacion (no "sa"). Por default "tickets_app".

.PARAMETER AppPassword
    Contrasena para el login de la aplicacion. Debe cumplir la politica de
    contrasenas de Windows (minimo 8 caracteres, con mayusculas, minusculas y
    numeros o simbolos).

.PARAMETER RunMigrate
    Si se incluye, corre "python manage.py migrate" al final contra la base
    recien creada, usando el entorno virtual del proyecto (venv/Scripts/python.exe).

.EXAMPLE
    .\bootstrap_db.ps1 -SaPassword "ContrasenaDeSa" -AppPassword "ContrasenaDeLaApp" -RunMigrate
#>

param(
    [string]$SqlInstance = "localhost\SQLEXPRESS",
    [Parameter(Mandatory = $true)][string]$SaPassword,
    [string]$DbName = "tickets_db",
    [string]$AppLogin = "tickets_app",
    [Parameter(Mandatory = $true)][string]$AppPassword,
    [switch]$RunMigrate
)

$ErrorActionPreference = "Stop"

function Invoke-Sql {
    param([string]$ConnectionString, [string]$Query)
    $conn = New-Object System.Data.SqlClient.SqlConnection
    $conn.ConnectionString = $ConnectionString
    $conn.Open()
    try {
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = $Query
        $cmd.ExecuteNonQuery() | Out-Null
    } finally {
        $conn.Close()
    }
}

$masterConnStr = "Server=$SqlInstance;Database=master;User Id=sa;Password=$SaPassword;TrustServerCertificate=True;"
$dbConnStr = "Server=$SqlInstance;Database=$DbName;User Id=sa;Password=$SaPassword;TrustServerCertificate=True;"

Write-Host "Creando base de datos '$DbName' (si no existe)..."
Invoke-Sql -ConnectionString $masterConnStr -Query "IF DB_ID('$DbName') IS NULL CREATE DATABASE [$DbName];"

Write-Host "Creando login '$AppLogin' (si no existe)..."
Invoke-Sql -ConnectionString $masterConnStr -Query "IF NOT EXISTS (SELECT * FROM sys.sql_logins WHERE name = '$AppLogin') CREATE LOGIN [$AppLogin] WITH PASSWORD = '$AppPassword', CHECK_POLICY = ON;"

Write-Host "Creando usuario dentro de '$DbName' y asignando permisos..."
Invoke-Sql -ConnectionString $dbConnStr -Query "IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '$AppLogin') BEGIN CREATE USER [$AppLogin] FOR LOGIN [$AppLogin]; ALTER ROLE db_owner ADD MEMBER [$AppLogin]; END"

Write-Host ""
Write-Host "Listo. Agrega esto a tu .env (si no lo tienes ya):"
Write-Host "DB_ENGINE=mssql"
Write-Host "DB_NAME=$DbName"
Write-Host "DB_USER=$AppLogin"
Write-Host "DB_PASSWORD=$AppPassword"
Write-Host "DB_HOST=$SqlInstance"

if ($RunMigrate) {
    $projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
    $pythonExe = Join-Path $projectRoot "venv\Scripts\python.exe"
    if (-not (Test-Path $pythonExe)) {
        Write-Warning "No se encontro el entorno virtual en $pythonExe. Corre 'python manage.py migrate' manualmente con las variables DB_* de arriba."
    } else {
        Write-Host ""
        Write-Host "Corriendo migraciones sobre '$DbName'..."
        $env:DB_ENGINE = "mssql"
        $env:DB_NAME = $DbName
        $env:DB_USER = $AppLogin
        $env:DB_PASSWORD = $AppPassword
        $env:DB_HOST = $SqlInstance
        Push-Location $projectRoot
        & $pythonExe manage.py migrate
        Pop-Location
    }
}
