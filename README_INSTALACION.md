# Guía de Instalación y Ejecución - Generador TSOL Distrijass

## 📋 Requisitos Previos

- **Python 3.8 o superior** instalado en el sistema
- Conexión a internet (solo para la instalación inicial)
- Archivo `PROVEE-TSOL.xlsx` en la ubicación configurada

## 🚀 Instalación (Primera Vez)

### Paso 1: Instalar el Entorno Virtual

Ejecute el archivo `instalar_entorno.bat` haciendo doble clic sobre él.

Este script:
- ✅ Verifica que Python esté instalado
- ✅ Crea el entorno virtual `venv`
- ✅ Instala todas las dependencias necesarias:
  - pandas
  - openpyxl
  - numpy

**Nota:** Este paso solo se realiza **UNA VEZ**, a menos que necesite reinstalar el entorno.

### Paso 2: Verificar Instalación

Después de ejecutar `instalar_entorno.bat`, debería ver:

```
========================================
INSTALACION COMPLETADA EXITOSAMENTE
========================================

El entorno virtual ha sido creado y configurado
Puede ejecutar 'run.bat' para procesar los archivos TSOL
```

## ▶️ Ejecución Normal

Una vez instalado el entorno, ejecute `run.bat` para procesar los archivos TSOL.

Este script:
- ✅ Verifica que el entorno virtual exista
- ✅ Activa automáticamente el entorno virtual
- ✅ Ejecuta el procesamiento TSOL
- ✅ Genera los archivos ZIP en `output_files/historico/`

## 📂 Estructura de Archivos

```
PlanosTsol_Distrijass/
├── instalar_entorno.bat      # Instalación inicial (ejecutar UNA VEZ)
├── run.bat                    # Ejecución normal (ejecutar cada vez)
├── PlanosTsol_Distrijass.py  # Script principal
├── config.json                # Configuración
├── venv/                      # Entorno virtual (creado por instalación)
└── output_files/
    └── historico/             # Archivos ZIP generados
```

## 🔧 Solución de Problemas

### Error: "Python no está instalado"
- Descargue e instale Python desde https://www.python.org/
- Durante la instalación, marque "Add Python to PATH"

### Error: "No se encuentra el entorno virtual"
- Ejecute `instalar_entorno.bat` primero
- Si persiste, elimine la carpeta `venv` y vuelva a ejecutar la instalación

### Error: "No se pudo activar el entorno virtual"
- Ejecute `instalar_entorno.bat` nuevamente
- Verifique permisos de escritura en la carpeta

## 📊 Archivos Generados

Después de ejecutar `run.bat`, encontrará en `output_files/historico/`:

- `DISTRIJASS_211688_YYYYMMDD.zip` - Archivos TSOL para Distrijass
- `DISTRIJASS_211697_YYYYMMDD.zip` - Archivos TSOL para Eje Cafetero

Cada ZIP contiene:
- `productos_*.txt` - Catálogo de productos
- `clientes_*.txt` - Base de clientes

## 🔄 Actualización de Dependencias

Si necesita actualizar las dependencias:

1. Elimine la carpeta `venv`
2. Ejecute `instalar_entorno.bat` nuevamente

## ⚙️ Configuración

Edite `config.json` para ajustar:
- Rutas de archivos fuente
- Códigos de empresas
- Filtros de proveedores
- Mapeo de columnas

---

**Versión:** 2.0  
**Última actualización:** Octubre 2025
