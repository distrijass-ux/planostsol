@echo off
echo ========================================
echo Generador TSOL Distrijass
echo ========================================
echo.
echo Seleccione que procesar:
echo   1. Solo DISTRIJASS CALI (211688)
echo   2. Solo EJE CAFETERO (211697)
echo   3. AMBAS empresas
echo   4. Salir
echo.
set /p opcion="Ingrese su opcion (1-4): "

if "%opcion%"=="4" goto :fin
if "%opcion%"=="3" goto :ambas
if "%opcion%"=="2" goto :eje
if "%opcion%"=="1" goto :distrijass

echo Opcion invalida
pause
exit /b 1

:distrijass
echo.
echo ========================================
echo Procesando DISTRIJASS CALI (211688)
echo ========================================
echo.
if not exist "venv\" (
    echo ERROR: El entorno virtual no existe.
    echo Por favor ejecuta primero: instalar_entorno.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python PlanosTsol_Distrijass.py
goto :finalizar

:eje
echo.
echo ========================================
echo Procesando EJE CAFETERO (211697)
echo ========================================
echo.
if not exist "venv\" (
    echo ERROR: El entorno virtual no existe.
    echo Por favor ejecuta primero: instalar_entorno.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python PlanosTsol_Eje.py
goto :finalizar

:ambas
echo.
echo ========================================
echo Procesando AMBAS empresas
echo ========================================
echo.
if not exist "venv\" (
    echo ERROR: El entorno virtual no existe.
    echo Por favor ejecuta primero: instalar_entorno.bat
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python ejecutar_todos.py
goto :finalizar

:finalizar
echo.
echo ========================================
echo Proceso completado
echo ========================================
pause
goto :fin

:fin
exit /b 0
