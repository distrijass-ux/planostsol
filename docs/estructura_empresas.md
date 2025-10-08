# Configuración por Empresa - Distrijass vs Eje Cafetero

## Estructura de archivos independientes por empresa

La configuración se ha actualizado para generar archivos completamente separados por empresa:

### Distrijass
- **Prefijo ZIP**: `DISTRIJASS_211688`
- **Carpeta salida**: `output_files/Distrijass/`
- **Usuario FTP**: `DISTRIJASS_211688`
- **Archivos maestros**: 
  - Clientes: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Distrijass//intercliente.txt`
  - Ciudades: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Distrijass//interciudad.txt`
  - Asesores: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Distrijass//interasesor.txt`
  - Supervisores: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Distrijass//intersupervisor.txt`

### Eje Cafetero
- **Prefijo ZIP**: `DISTRIJASS_211697`
- **Carpeta salida**: `output_files/Eje/`
- **Usuario FTP**: `DISTRIJASS_211697`
- **Archivos maestros**:
  - Clientes: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Eje//intercliente.txt`
  - Ciudades: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Eje//interciudad.txt`
  - Asesores: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Eje//interasesor.txt`
  - Supervisores: `D://Distrijass//Sistema Info//Información//Envío TSOL//TSOL//Eje//intersupervisor.txt`

## Filtros aplicados

- **Distrijass**: Filtra por `Portafolio = "Distrijass"`
- **Eje Cafetero**: Filtra por `Portafolio = "Eje"`

## Clasificación de clientes

La clasificación de clientes (TE, TT, MM, SN) se toma directamente de:
1. **Archivo mm.xlsx**: Define clientes MM vs SN según la columna de tipología
2. **Archivo TE Viejos**: Lista de clientes catalogados como Tienda Especializada
3. **Por defecto**: Los demás se clasifican como TT (Tienda a Tienda)

La prioridad es: MM > SN > TE > TT

## Archivos generados por empresa

Cada empresa generará su propio conjunto completo:
- `ventas.txt`
- `Listado de Facturas.txt`
- `Totales de Control.txt`
- `Vendedores.txt`
- `Supervisores.txt`
- `Tipos De Negocio.txt`
- `SKU (Productos).txt`
- `Clientes.txt`
- `Municipios.txt`
- `Inventario.txt`
- `Barrios.txt`
- `Rutas.txt`

Y su respectivo ZIP comprimido en la carpeta `historico/` de cada empresa.

## Ventajas de esta estructura

1. **Separación clara**: Cada empresa tiene sus archivos completamente independientes
2. **Trazabilidad**: Los logs y errores se identifican por empresa
3. **Envío FTP independiente**: Cada empresa puede tener credenciales y configuraciones FTP diferentes
4. **Escalabilidad**: Fácil agregar nuevas empresas del grupo
5. **Compatibilidad TSOL**: Cada empresa se ve como un distribuidor independiente en TSOL