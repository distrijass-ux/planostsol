# ====================================================================
# Script PowerShell automatico para generar archivos TSOL - DISTRIJASS CALI
# Empresa: DISTRIJASS CALI (NIT: 211688)
# Para uso en tareas programadas - SIN INTERACCION DE USUARIO
# ====================================================================

# Configurar variables de fecha y hora para logging
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Crear directorio de logs si no existe
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

$logFile = "logs\tsol_cali_$timestamp.log"

# Función para logging
function Write-Log {
    param($message)
    $logEntry = "$logDate - $message"
    Write-Output $logEntry
    Add-Content -Path $logFile -Value $logEntry
}

Write-Log "Iniciando generacion TSOL DISTRIJASS CALI"

# Verificar si existe el entorno virtual
if (!(Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Log "ERROR: No se encontro el entorno virtual"
    exit 1
}

# Verificar si existe el archivo principal
if (!(Test-Path "PlanosTsol_Distrijass.py")) {
    Write-Log "ERROR: No se encontro PlanosTsol_Distrijass.py"
    exit 1
}

Write-Log "Activando entorno virtual"
try {
    & "venv\Scripts\Activate.ps1"
    
    Write-Log "Verificando dependencias"
    & python -c "import pandas, openpyxl" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Instalando dependencias faltantes"
        & pip install pandas openpyxl *>&1 | Add-Content -Path $logFile
    }

    Write-Log "Ejecutando PlanosTsol_Distrijass.py"
    & python PlanosTsol_Distrijass.py *>&1 | Add-Content -Path $logFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "EXITO: Archivos TSOL generados correctamente"
        Write-Log "Archivo ZIP creado en: output_files\Distrijass\historico\"
        Write-Log "Proceso completado exitosamente"
        exit 0
    } else {
        Write-Log "ERROR: Fallo en la ejecucion del script"
        exit 1
    }
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    exit 1
}