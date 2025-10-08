# Generador TSOL Distrijass - Arquitectura Separada

## Estructura del Proyecto

El proyecto ahora está dividido en **dos archivos independientes** para evitar confusiones:

### Archivos Principales

1. **`PlanosTsol_Distrijass.py`**
   - Procesa: **DISTRIJASS CALI (NIT 211688)**
   - Output: `output_files/Distrijass/`
   - Log: `distrijass_cali.log`
   - Proveedores: Colgate, Papeles, Colombiana, Henkel, Bayer, etc.

2. **`PlanosTsol_Eje.py`**
   - Procesa: **DISTRIJASS EJE CAFETERO (NIT 211697)**
   - Output: `output_files/Eje/`
   - Log: `distrijass_eje.log`
   - Proveedores: Distrijass, Productos, Levapan, Pisa, Solla, etc.

3. **`ejecutar_todos.py`**
   - Script opcional que ejecuta ambas empresas secuencialmente
   - Muestra resumen al final

### Archivos de Configuración

- **`config.json`**: Configuración única para ambas empresas
  - `companies.distrijass`: Config de CALI
  - `companies.eje_cafetero`: Config de EJE
  - `files`: Archivos compartidos (ventas, PROVEE-TSOL, inventario, etc.)

### Scripts de Ejecución

- **`instalar_entorno.bat`**: Instalación única del entorno virtual
- **`run.bat`**: Menú interactivo con opciones:
  1. Solo Distrijass Cali
  2. Solo Eje Cafetero
  3. Ambas empresas
  4. Salir

## Integración con PROVEE-TSOL.xlsx

Ambos archivos utilizan la misma lógica centralizada:

### Productos (SKU)
- Hoja: `PRODUCTO`
- Filtro: Por columna `Proveedor` según lista de cada empresa
- Campos: Codigo SAP, Nombre, Codigo de barras

### Clientes
- Origen: Archivos `intercliente.txt` (uno por empresa)
- **Tipo de Negocio**: Se cruza con hoja `TIPOLOGIA` de PROVEE-TSOL
- **Filtro**: Solo clientes con ventas reales
- Normalización de códigos: á→a, tildes eliminadas

### Tipología de Negocio
- Hoja: `TIPOLOGIA`
- Campos: Cod. necesidad, Nom. necesidad
- Se normaliza para evitar problemas con tildes

## Cómo Ejecutar

### Opción 1: Ejecutar una empresa específica

```bash
# Solo CALI
.\venv\Scripts\python.exe PlanosTsol_Distrijass.py

# Solo EJE
.\venv\Scripts\python.exe PlanosTsol_Eje.py
```

### Opción 2: Ejecutar ambas empresas

```bash
.\venv\Scripts\python.exe ejecutar_todos.py
```

### Opción 3: Usar el menú interactivo

```bash
.\run.bat
```

## Estructura de Salida

```
output_files/
├── Distrijass/           # CALI (211688)
│   ├── ventas.txt
│   ├── Clientes.txt
│   ├── SKU (Productos).txt
│   ├── Tipos De Negocio.txt
│   ├── ... (otros archivos TSOL)
│   └── historico/
│       └── DISTRIJASS_211688_20256MMDD.zip
│
└── Eje/                  # EJE CAFETERO (211697)
    ├── ventas.txt
    ├── Clientes.txt
    ├── SKU (Productos).txt
    ├── Tipos De Negocio.txt
    ├── ... (otros archivos TSOL)
    └── historico/
        └── DISTRIJASS_211697_20256MMDD.zip
```

## Logs Independientes

- `distrijass_cali.log`: Log detallado de CALI
- `distrijass_eje.log`: Log detallado de EJE CAFETERO

## Ventajas de la Arquitectura Separada

✅ **Claridad**: Cada archivo tiene una responsabilidad única
✅ **Mantenimiento**: Cambios en una empresa no afectan la otra
✅ **Debugging**: Logs y outputs separados facilitan troubleshooting
✅ **Ejecución Flexible**: Procesar solo lo que necesitas
✅ **Sin Confusiones**: No hay mezcla de lógicas entre empresas

## Cambios Respecto a la Versión Original (Colgate)

1. **Tipo de Negocio**: Ya no usa archivos `TE Viejos` o `mm.xlsx`, todo viene de PROVEE-TSOL TIPOLOGIA
2. **Multi-empresa**: Soporta dos empresas con configuraciones independientes
3. **Filtro de Clientes**: Solo exporta clientes que tengan ventas reales
4. **Normalización**: Maneja tildes y caracteres especiales automáticamente
5. **Fecha**: Extrae la fecha máxima de los datos de ventas (no usa fecha actual)

## Archivos de Respaldo

- `PlanosTsol_Distrijass_CORRUPTO.bak`: Versión corrupta anterior
- `PlanosTsol_Distrijass_backup.py`: Backup del intento anterior
- `PlanosTsol_Distrijass_FIXED.py`: Primera versión unificada
- `run_old.bat`: Script run anterior sin menú

## Notas Importantes

⚠️ **Ambas empresas usan el mismo archivo de ventas**: `Info proveedores.xlsx`
⚠️ **Proveedores diferentes**: El filtro de proveedores es distinto para cada empresa
⚠️ **Archivos inter* diferentes**: Cada empresa tiene sus propios intercliente, interasesor, etc.
⚠️ **PROVEE-TSOL compartido**: Ambas usan la misma hoja TIPOLOGIA y PRODUCTO

## Troubleshooting

### Error: "No se encontraron datos"
- Verificar que `Info proveedores.xlsx` existe y tiene hoja `infoventas`
- Verificar que los proveedores en `config.json` coinciden con los del archivo

### Error: "Archivo inter* no encontrado"
- Verificar rutas en `config.json` sección `paths` de cada empresa

### Error: "No se generaron clientes"
- Verificar que hay ventas para el período
- Verificar que los clientes existen en `intercliente.txt`

### Error: "Tipo de Negocio no encontrado"
- Verificar que PROVEE-TSOL.xlsx tiene la hoja TIPOLOGIA
- Verificar columnas `Cod. necesidad` y `Nom. necesidad`
