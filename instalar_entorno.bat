@echo off
echo ========================================
echo Instalacion del Entorno Virtual
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instale Python desde https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Python detectado correctamente
python --version
echo.

REM Verificar si ya existe el entorno virtual
if exist "venv\" (
    echo.
    echo ADVERTENCIA: Ya existe un entorno virtual en esta carpeta
    set /p RESPUESTA="Desea eliminarlo y crear uno nuevo? (S/N): "
    if /i "%RESPUESTA%"=="S" (
        echo Eliminando entorno virtual anterior...
        rmdir /s /q venv
    ) else (
        echo Instalacion cancelada
        pause
        exit /b 0
    )
)

echo [2/4] Creando entorno virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)
echo Entorno virtual creado exitosamente
echo.

echo [3/4] Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)
echo Entorno virtual activado
echo.

echo [4/4] Instalando dependencias...
echo Actualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando paquetes requeridos:
echo - pandas
echo - openpyxl
echo - numpy
echo.

pip install pandas openpyxl numpy
if %errorlevel% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo ========================================
echo INSTALACION COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo El entorno virtual ha sido creado y configurado
echo Puede ejecutar 'ejecutar_planos.bat' para procesar los archivos TSOL
echo.
pause
