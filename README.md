# PlanosTsol Distrijass

Sistema automatizado para la generación de archivos TSOL (Track Sales Online) para las empresas del grupo Distrijass.

## 📋 Descripción

Este proyecto genera archivos de ventas en formato TSOL compatible con el sistema Track Sales Online, específicamente para:

- **DISTRIJASS CALI** (NIT: 211688)
- **EJE CAFETERO** (NIT: 211697)

## 🚀 Características

- ✅ **100% Conforme TSOL**: Cumple todas las especificaciones oficiales
- ✅ **Generación Automática**: 12 archivos por empresa
- ✅ **Datos Reales**: Integración con PROVEE-TSOL.xlsx
- ✅ **Geolocalización**: Coordenadas Valle del Cauca
- ✅ **Logging Completo**: Trazabilidad de procesos
- ✅ **Tareas Programadas**: Scripts para automatización

## 📦 Archivos Generados

| Archivo | Registros | Descripción |
|---------|-----------|-------------|
| Municipios.txt | 121 | Municipios Valle del Cauca |
| Tipos De Negocio.txt | 17 | Tipología de clientes |
| Supervisores.txt | 21 | Supervisores con sedes |
| Vendedores.txt | 163 | Vendedores activos |
| SKU (Productos).txt | 6,920 | Productos PROVEE-TSOL |
| Rutas.txt | 16,635 | Rutas comerciales |
| Clientes.txt | 15,375 | Clientes georreferenciados |
| Inventario.txt | 929 | Productos en stock |
| ventas.txt | 74,477 | Transacciones de venta |
| Totales de Control.txt | 1 | Validación matemática |
| Listado de Facturas.txt | - | Resumen facturas |

## 🛠️ Instalación

### Requisitos Previos
- Python 3.8+
- Windows 10/11
- PowerShell 5.1+

### Instalación Automática
```bash
.\instalar_entorno.bat
```

### Instalación Manual
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🔧 Uso

### Ejecución Manual
```bash
# Activar entorno virtual
venv\Scripts\activate

# Ejecutar generación
python PlanosTsol_Distrijass.py  # Solo DISTRIJASS CALI
python PlanosTsol_Eje.py         # Solo EJE CAFETERO
python ejecutar_todos.py         # Ambas empresas
```

### Ejecución con Scripts
```bash
# Menu interactivo
.\run.bat

# Solo DISTRIJASS CALI (automático)
.\run_cali.bat          # CMD/Batch
.\run_cali.ps1          # PowerShell (Recomendado)
```

### Tareas Programadas
**PowerShell (Recomendado):**
```
Programa: PowerShell.exe
Argumentos: -ExecutionPolicy Bypass -File "D:\Desarrollo\PlanosTsol_Distrijass\run_cali.ps1"
Directorio: D:\Desarrollo\PlanosTsol_Distrijass
```

## 📁 Estructura del Proyecto

```
PlanosTsol_Distrijass/
├── PlanosTsol_Distrijass.py    # Script principal DISTRIJASS CALI
├── PlanosTsol_Eje.py           # Script principal EJE CAFETERO
├── ejecutar_todos.py           # Ejecutor para ambas empresas
├── config.json                 # Configuración FTP y parámetros
├── requirements.txt            # Dependencias Python
├── run_cali.ps1               # Script automático PowerShell
├── run_cali.bat               # Script automático Batch
├── run.bat                    # Menu interactivo
├── instalar_entorno.bat       # Instalador automático
├── docs/                      # Documentación técnica
├── tsol/                      # Especificaciones TSOL
└── output_files/              # Archivos generados (git ignore)
    ├── Distrijass/
    └── Eje_Cafetero/
```

## 📊 Salida

Los archivos se generan en formato ZIP:
- **DISTRIJASS**: `output_files/Distrijass/historico/DISTRIJASS_211688_YYYYMMDD.zip`
- **EJE CAFETERO**: `output_files/Eje_Cafetero/historico/EJE_CAFETERO_211697_YYYYMMDD.zip`

## 🔍 Logging

Los logs se generan en:
- `logs/tsol_cali_YYYY-MM-DD_HH-mm-ss.log` (PowerShell)
- `logs/tsol_cali_output.log` (Batch)

## 🏢 Empresas Configuradas

### DISTRIJASS CALI (NIT: 211688)
- **Cobertura**: Valle del Cauca
- **Sedes**: PALMIRA/CALI, TULUA, POPAYAN, BUENAVENTURA
- **Municipios**: 121
- **Geolocalización**: -76.3, 3.45

### EJE CAFETERO (NIT: 211697)
- **Cobertura**: Eje Cafetero
- **Sedes**: PEREIRA, MANIZALES, ARMENIA
- **Municipios**: Configurables

## 📋 Especificaciones TSOL

El sistema cumple 100% con las especificaciones oficiales TSOL:
- ✅ 1.1 Municipios
- ✅ 1.2 Tipos De Negocio  
- ✅ 1.3 Supervisores
- ✅ 1.4 Vendedores
- ✅ 1.5 SKU (Productos)
- ✅ 1.6 Rutas
- ✅ 1.7 Clientes
- ✅ 1.8 Inventario
- ✅ 1.9 Ventas
- ✅ 1.10 Totales de Control

## 🔧 Mantenimiento

Para actualizar datos:
1. Actualizar `PROVEE-TSOL.xlsx` con nuevos productos
2. Ejecutar scripts de generación
3. Verificar logs para validar proceso

## 📞 Soporte

Para soporte técnico, revisar:
- `docs/` - Documentación técnica
- `logs/` - Archivos de log
- Especificaciones TSOL en `tsol/`

## 📄 Licencia

Proyecto interno Grupo Distrijass - 2025