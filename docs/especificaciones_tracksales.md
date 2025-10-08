# Especificaciones TrackSales 3.7.2.3

Este documento resume los requisitos definidos por TSOL para la entrega de información de la distribuidora, según la especificación **TrackSales 3.7.2.3**. Sirve como referencia para validar los datos generados por los procesos automáticos.

## 1. Información solicitada

### 1.1 Municipios
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Identificador del municipio | Sí |
| Nombre | Carácter | Nombre del municipio | Sí |

### 1.2 Tipos de Negocio
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Identificador del tipo de negocio | Sí |
| Nombre | Carácter | Descripción del tipo de negocio | Sí |

### 1.3 Supervisores
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Código del supervisor | Sí |
| Nombre | Carácter | Nombre del supervisor | Sí |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |

### 1.4 Vendedores
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Código del vendedor | Sí |
| Nombre | Carácter | Nombre del vendedor | Sí |
| Ubicación | Carácter | Zona geográfica atendida | No |
| Cédula | Carácter | Documento del vendedor | Sí |
| Código Supervisor | Carácter | Supervisor asignado | Sí |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |

### 1.5 SKU (Productos)
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Código interno de la referencia | Sí |
| Nombre | Carácter | Nombre de la referencia | Sí |
| Tipo Referencia | Carácter | RG (regular), OF (promocional), OB (obsequio) | Sí |
| Tipo de Unidad | Carácter | Unidad de venta (ej. UND, CAJ) | Sí |
| Código de Barras | Carácter | Código de barras (solo aplica a RG) | Sí |
| Código Categoría | Carácter | Código de la categoría | Sí |
| Nombre Categoría | Carácter | Nombre de la categoría | Sí |
| Código Subcategoría | Carácter | Código de la subcategoría | Sí |
| Nombre Subcategoría | Carácter | Nombre de la subcategoría | Sí |
| Factor Conversión Unidad | Numérico | Cantidad de unidades simples por presentación | No |
| Factor Peso | Numérico | Factor para convertir a kilos | No |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |

### 1.6 Rutas
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código Vendedor | Carácter | Código del vendedor | Sí |
| Código Cliente | Carácter | Código del cliente | Sí |
| Mes | Carácter | Mes planificado (1–12) | No |
| Día Semana | Carácter | Día planificado (1=Lunes, …, 7=Domingo) | Sí |
| Frecuencia | Carácter | 1=mensual, 2=quincenal, 3=tri-semanal, 4=semanal | Sí |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |
| Identificador de sucursal | Carácter | Id. de la sucursal del cliente | Sí |

### 1.7 Clientes
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código | Carácter | Código del cliente | Sí |
| Nombre | Carácter | Nombre del cliente | Sí |
| Fecha Ingreso | Carácter | Fecha de creación (DDMMYYYY); si falta usar fecha sistema | No |
| NIT | Carácter | NIT del cliente | Sí |
| Dirección | Carácter | Dirección | Sí |
| Teléfono | Carácter | Teléfono | No |
| Representante Legal | Carácter | Representante legal | No |
| Código Municipio | Carácter | Municipio donde opera | Sí |
| Código Tipo Negocio | Carácter | Tipo de negocio (rel. con tabla 1.2) | Sí |
| Estrato | Carácter | Estrato socioeconómico (1–7) | No |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |
| Ubicación longitud | Numérico (2 enteros, 6 decimales) | Longitud geográfica | Sí |
| Ubicación latitud | Numérico (2 enteros, 6 decimales) | Latitud geográfica | Sí |
| Identificador de sucursal | Carácter | Id. de la sucursal en la distribuidora | Sí |

### 1.8 Inventario
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Fecha | Carácter | Fecha del inventario (DDMMYYYY) | Sí |
| Código Producto | Carácter | Código del producto | Sí |
| Cantidad | Carácter | Inventario disponible | Sí |
| Unidad de Medida | Carácter | Unidad de la cantidad | Sí |
| Código de Bodega | Carácter | Identificador de la bodega | Sí |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |

### 1.9 Ventas
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código Cliente | Carácter | Cliente facturado | Sí |
| Código Vendedor | Carácter | Vendedor responsable | Sí |
| Código Producto (SKU) | Carácter | Producto vendido | Sí |
| Fecha | Carácter | Fecha de venta o devolución (DDMMYYYY) | Sí |
| Número Documento | Carácter | Número de factura | Sí |
| Cantidad | Numérico | Unidades vendidas/devolvidas | Sí |
| Valor Total Item Vendido | Numérico | Valor sin impuestos | Sí |
| Tipo | Carácter | 0=Venta, 1=Dev. buen estado, 2=Dev. mal estado | Sí |
| Costo | Numérico | Costo del item | Sí |
| Unidad de Medida | Carácter | Unidad de la transacción | Sí |

### 1.10 Totales de Control
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Descriptor Total | Carácter | Siempre `TotalValorVenta` | Sí |
| Valor | Numérico | Total del valor de ventas reportado | Sí |

### 1.11 Sell In
| Campo | Tipo | Descripción | Obligatorio |
| --- | --- | --- | --- |
| Código Producto (SKU) | Carácter | Producto comprado | Sí |
| Fecha | Carácter | Fecha de compra (DDMMYYYY) | Sí |
| Número Documento | Carácter | Número de factura | Sí |
| Cantidad Sell In | Numérico | Unidades compradas | Sí |
| Valor Total Item Comprado | Numérico | Valor sin impuestos | Sí |
| Unidad de Medida | Carácter | Unidad de la compra | Sí |
| Código Sede | Carácter | Identificador de la sede | Sí |
| Nombre Sede | Carácter | Nombre de la sede | Sí |

## 2. Métodos de extracción
- **Archivos planos**: separador `{`.
- **Totales de control**: no se incluyen registros de totales dentro de los archivos principales.

## 3. Automatización
TSOL permite automatizar la carga mediante procesos programados. Es necesario coordinar con TSOL los procesos de extracción, transmisión por FTP, retroalimentación, contingencias y programación de envíos.

## 4. Aclaraciones generales
- Fechas en formato texto `DDMMYYYY`.
- Horas en formato `HH:MM:SS` (24 horas).
- Números con punto (`.`) como separador decimal y sin separador de miles.
- La información debe ser consistente: por ejemplo, no reportar ventas de clientes inexistentes o productos sin definición en el maestro correspondiente.
- La unidad de medida debe ser uniforme para cada SKU en todas las tablas (ventas, inventario, sell in, etc.).
- Las ventas se informan antes de IVA.
- Cada conjunto de información puede extraerse por métodos diferentes, siempre respetando la norma anterior.

## 5. Ejemplos
La especificación incluye ejemplos de archivos para cada tabla (municipios, tipos de negocio, supervisores, vendedores, SKU, rutas, clientes, inventario, ventas, totales de control y sell in). Se recomienda generar muestras con el mismo separador `{` y el orden de campos descrito en las secciones anteriores.
