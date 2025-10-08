@echo off
:: ====================================================================
:: Script automatico para generar archivos TSOL - DISTRIJASS CALI
:: Empresa: DISTRIJASS CALI (NIT: 211688)
:: Para uso en tareas programadas - SIN INTERACCION DE USUARIO
:: ====================================================================

:: Crear directorio de logs si no existe
if not exist "logs" mkdir logs

:: Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: No se encontro el entorno virtual >> logs\tsol_cali_error.log
    exit /b 1
)

:: Verificar si existe el archivo principal
if not exist "PlanosTsol_Distrijass.py" (
    echo ERROR: No se encontro PlanosTsol_Distrijass.py >> logs\tsol_cali_error.log
    exit /b 1
)

:: Activar entorno virtual silenciosamente
call venv\Scripts\activate.bat >nul 2>&1

:: Verificar dependencias silenciosamente
python -c "import pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias faltantes >> logs\tsol_cali_install.log
    pip install pandas openpyxl >>logs\tsol_cali_install.log 2>&1
)

:: Ejecutar el script principal y capturar salida
python PlanosTsol_Distrijass.py >logs\tsol_cali_output.log 2>&1

:: Verificar resultado de la ejecución
if errorlevel 1 (
    echo ERROR: Fallo en la ejecucion del script >> logs\tsol_cali_error.log
    exit /b 1
) else (
    echo EXITO: Archivos TSOL generados correctamente >> logs\tsol_cali_success.log
    echo Archivo ZIP creado en: output_files\Distrijass\historico\ >> logs\tsol_cali_success.log
)

:: Finalizar sin pausas
exit /b 0