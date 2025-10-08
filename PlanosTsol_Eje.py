# PlanosTsol_Eje.py
# Generador de archivos TSOL para DISTRIJASS EJE CAFETERO (NIT 211697)
# Basado en PlanosTsol_Colgate.py
# Integrado con PROVEE-TSOL.xlsx para productos, clientes y tipología

import pandas as pd
import os
from datetime import datetime
import logging
import re
import json
import zipfile
import ftplib
import calendar
import shutil

# Configuración del logging
logging.basicConfig(
    filename='distrijass_eje.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

class VentaProcessor:
    def __init__(self, config_path):
        self.config = self._cargar_configuracion(config_path)
        # Usar configuración de empresa 'eje_cafetero'
        self.company_config = self.config['companies']['eje_cafetero']
        
        self.ventas_path = self.config['files'].get('ventas')
        self.output_folder = os.path.join(
            self.config.get('output_folder', 'output_files'),
            self.company_config['output_subfolder']
        )
        self.catalogo_principal = self.config['files']['catalogo_principal']
        
        # Proveedores desde filtro_proveedores.criterios
        self.proveedores = self.company_config.get('filtro_proveedores', {}).get('criterios', [])
        
        # Mes y año se determinarán dinámicamente desde los datos del Excel
        self.mes = None
        self.ano = None
        self.filtered_data = None
        self._crear_carpeta_salida()

    def _cargar_configuracion(self, config_path):
        """Carga la configuración desde un archivo JSON."""
        if not os.path.isfile(config_path):
            logger.error(f"Archivo de configuración no encontrado: {config_path}")
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = json.load(file)
                logger.info("Configuración cargada exitosamente.")
                return config
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {e}")
            raise

    def _crear_carpeta_salida(self):
        """Crea la carpeta de salida si no existe."""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            logger.info(f"Carpeta de salida creada: {self.output_folder}")
        else:
            logger.info(f"Carpeta de salida ya existe: {self.output_folder}")

    @staticmethod
    def verificar_archivo(archivo):
        """Verifica que el archivo exista y sea accesible."""
        if not os.path.isfile(archivo):
            logger.error(f"Archivo no encontrado: {archivo}")
            raise FileNotFoundError(f"Archivo no encontrado: {archivo}")
        logger.info(f"Archivo encontrado: {archivo}")
        return archivo

    def cargar_y_filtrar_datos_por_periodo(self):
        """Carga los datos y filtra por el período especificado y proveedores."""
        self.verificar_archivo(self.ventas_path)

        try:
            # Cargar todos los datos primero para determinar la fecha más reciente
            all_data = pd.read_excel(
                self.ventas_path,
                sheet_name='infoventas',
                parse_dates=['Fecha']
            )
            
            # Encontrar la fecha más reciente en los datos
            if all_data.empty or 'Fecha' not in all_data.columns:
                logger.error("No se encontraron datos o la columna 'Fecha' no existe")
                raise ValueError("No se encontraron datos válidos en el archivo Excel")
            
            fecha_maxima = all_data['Fecha'].max()
            self.mes = fecha_maxima.month
            self.ano = fecha_maxima.year
            
            logger.info(f"Fecha más reciente encontrada: {fecha_maxima}")
            logger.info(f"Mes y año determinados: Mes {self.mes}, Año {self.ano}")
            
            # Ahora filtrar por el período determinado
            self.filtered_data = all_data[
                (all_data['Fecha'].dt.month == self.mes) &
                (all_data['Fecha'].dt.year == self.ano)
            ]
            logger.info(f"Datos filtrados por período: Mes {self.mes}, Año {self.ano}.")

            # Filtrar por proveedores si están definidos
            if self.proveedores:
                regex_pattern = '|'.join([re.escape(proveedor) for proveedor in self.proveedores])
                self.filtered_data = self.filtered_data[self.filtered_data['Proveedor'].str.contains(regex_pattern, case=False, na=False)]
                logger.info(f"Datos filtrados por proveedores: {self.proveedores}")
            else:
                logger.warning("No se especificaron proveedores para filtrar.")
        except Exception as e:
            logger.error(f"Error al cargar y filtrar los datos: {e}")
            raise

    def procesar_datos(self):
        """Procesa los datos para preparar los campos necesarios según las especificaciones."""
        if self.filtered_data is None:
            raise ValueError("Los datos no están cargados o filtrados. Ejecute 'cargar_y_filtrar_datos_por_periodo' primero.")

        try:
            columnas_requeridas = [
                'Cod. cliente', 'Cod. vendedor', 'Cod. productto',
                'Fecha', 'Fac. numero', 'Cantidad', 'Vta neta',
                'Tipo', 'Costo', 'Unidad', 'Pedido'
            ]

            # Validar columnas requeridas
            for columna in columnas_requeridas:
                if columna not in self.filtered_data.columns:
                    logger.error(f"Columna requerida no encontrada: {columna}")
                    raise KeyError(f"Columna requerida no encontrada: {columna}")

            # Filtrar y renombrar columnas
            self.filtered_data = self.filtered_data[columnas_requeridas].rename(columns={
                'Cod. cliente': 'Código Cliente',
                'Cod. vendedor': 'Código Vendedor',
                'Cod. productto': 'Código Producto (Sku)',
                'Fecha': 'Fecha',
                'Fac. numero': 'Numero Documento',
                'Cantidad': 'Cantidad',
                'Vta neta': 'Valor Total Item Vendido',
                'Tipo': 'Tipo',
                'Costo': 'Costo',
                'Unidad': 'Unidad de Medida',
                'Pedido': 'Numero Único de Pedido'
            })

            # Convertir tipos y ajustar formato
            self.filtered_data['Código Vendedor'] = self.filtered_data['Código Vendedor'].astype(str)
            self.filtered_data['Código Producto (Sku)'] = self.filtered_data['Código Producto (Sku)'].astype(str).str.strip().str.upper()
            self.filtered_data['Fecha'] = self.filtered_data['Fecha'].dt.strftime('%Y/%m/%d')
            self.filtered_data['Numero Documento'] = self.filtered_data['Numero Documento'].astype(str)
            self.filtered_data['Tipo'] = self.filtered_data['Tipo'].astype(str)
            self.filtered_data['Cantidad'] = self.filtered_data['Cantidad'].astype(int)
            self.filtered_data['Valor Total Item Vendido'] = pd.to_numeric(self.filtered_data['Valor Total Item Vendido'], errors='coerce').round(2)
            self.filtered_data['Costo'] = pd.to_numeric(self.filtered_data['Costo'], errors='coerce').round(2)
            
            # Reemplazar guiones en Código Cliente con "999"
            self.filtered_data['Código Cliente'] = self.filtered_data['Código Cliente'].apply(
                lambda x: str(x).replace('-', '999')
            )
            
            self.filtered_data_total = self.filtered_data.copy()
            
            # Limpieza de la columna 'Código Cliente'
            self.filtered_data_total['Código Cliente'] = (
                self.filtered_data_total['Código Cliente']
                .astype(str)
                .str.strip()
                .str.replace('-', '999')
                .str.replace('"', '')
                .str.replace("'", '')
            )

            # Limpieza de la columna 'Código Producto (Sku)'
            self.filtered_data_total['Código Producto (Sku)'] = (
                self.filtered_data_total['Código Producto (Sku)']
                .astype(str)
                .str.strip()
                .str.replace('"', '')
                .str.replace("'", '')
            )
            
            # Alternativa: Multiplicar por -1 para garantizar que los valores sean positivos cuando Tipo == 1
            mask = self.filtered_data['Tipo'] == '1'
            self.filtered_data.loc[mask, 'Cantidad'] = self.filtered_data.loc[mask, 'Cantidad'].apply(lambda x: x * -1 if x < 0 else x)
            self.filtered_data.loc[mask, 'Valor Total Item Vendido'] = self.filtered_data.loc[mask, 'Valor Total Item Vendido'].apply(lambda x: x * -1 if x < 0 else x)
            self.filtered_data.loc[mask, 'Costo'] = self.filtered_data.loc[mask, 'Costo'].apply(lambda x: x * -1 if x < 0 else x)

            logger.info("Datos procesados exitosamente.")
        except Exception as e:
            logger.error(f"Error al procesar los datos: {e}")
            raise

    def guardar_archivo_ventas(self):
        """Guarda los datos procesados en archivos delimitados por '{' y en formato Excel."""
        if self.filtered_data is None:
            raise ValueError("Los datos no están procesados. Ejecute 'procesar_datos' primero.")

        try:
            # Ruta para el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'ventas.txt')

            # Guardar el archivo TXT
            txt_data = self.filtered_data.copy()
            txt_data['Valor Total Item Vendido'] = txt_data['Valor Total Item Vendido'].map(
                lambda x: f"{x:.2f}".replace('.', ',')
            )
            txt_data['Costo'] = txt_data['Costo'].map(
                lambda x: f"{x:.2f}".replace('.', ',')
            )
            txt_columns = [
                'Código Cliente', 'Código Vendedor', 'Código Producto (Sku)',
                'Fecha', 'Numero Documento', 'Cantidad',
                'Valor Total Item Vendido', 'Tipo', 'Costo', 'Unidad de Medida', 'Numero Único de Pedido'
            ]
            encabezado = '{'.join(txt_columns)
            with open(output_path_txt, 'w', encoding='utf-8') as file:
                file.write(encabezado + '\n')
                for _, row in txt_data[txt_columns].iterrows():
                    file.write('{'.join(row.astype(str)) + '\n')
            logger.info(f"Archivo TXT guardado exitosamente en: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al guardar los archivos: {e}")
            raise

    def generar_listado_facturas(self):
        """Genera el archivo 'Listado de Facturas' en formato TXT y Excel."""
        if self.filtered_data_total is None:
            raise ValueError("Los datos no están procesados. Ejecute 'cargar_y_filtrar_datos_por_periodo' y 'procesar_datos' primero.")

        try:
            # Validar columnas necesarias
            required_columns = ['Código Cliente', 'Código Vendedor', 'Fecha', 'Numero Documento', 'Valor Total Item Vendido', 'Costo']
            missing_columns = [col for col in required_columns if col not in self.filtered_data_total.columns]
            if missing_columns:
                raise KeyError(f"Las siguientes columnas están ausentes: {', '.join(missing_columns)}")

            # Agrupar datos por las columnas requeridas
            facturas_resumen = self.filtered_data_total.groupby(
                ['Código Cliente', 'Código Vendedor', 'Fecha', 'Numero Documento']
            ).agg(
                Valor_Total_Factura=('Valor Total Item Vendido', 'sum'),
                Valor_Facturado_Casa_Comercial=('Valor Total Item Vendido', 'sum')
            ).reset_index()

            # Convertir valores a formato con dos decimales
            facturas_resumen['Valor_Total_Factura'] = facturas_resumen['Valor_Total_Factura'].round(2)
            facturas_resumen['Valor_Facturado_Casa_Comercial'] = facturas_resumen['Valor_Facturado_Casa_Comercial'].round(2)

            # Ruta para los archivos de salida
            output_txt = os.path.join(self.output_folder, 'Listado de Facturas.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(facturas_resumen.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in facturas_resumen.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

        except Exception as e:
            logger.error(f"Error al generar el listado de facturas: {e}")
            raise

    def generar_totales_de_control(self):
        """Genera el archivo 'Totales de Control' en formato TXT y Excel."""
        if self.filtered_data_total is None:
            raise ValueError("Los datos no están procesados. Ejecute 'procesar_datos' primero.")

        try:
            # Calcular el total antes de cualquier conversión
            total_valor_venta = self.filtered_data_total['Valor Total Item Vendido'].sum()

            # Crear el DataFrame con los resultados
            totales_control = pd.DataFrame({
                'Descriptor Total': ['TotalValorVenta'],
                'Valor': [round(total_valor_venta, 2)]
            })

            # Ruta para los archivos de salida
            output_txt = os.path.join(self.output_folder, 'Totales de Control.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(totales_control.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in totales_control.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

        except Exception as e:
            logger.error(f"Error al generar los totales de control: {e}")
            raise

    def generar_vendedores(self):
        """Genera el archivo 'Vendedores' cruzando los datos de ventas con interasesor.txt."""
        try:
            # Ruta del archivo interasesor desde config
            interasesor_path = self.company_config['paths']['interasesor']
            
            # Verificar que el archivo exista
            self.verificar_archivo(interasesor_path)

            # Cargar los datos de interasesor.txt
            interasesor_data = pd.read_csv(
                interasesor_path,
                sep='{',
                engine='python',
                encoding='latin1',
                names=["Codigo", "Documento", "Nombre", "Apellido", "Telefono", "Direccion",
                       "Cargo", "Portafolio", "Estado", "Codigo supervisor", "Codigo bodega"]
            )

            # Filtrar solo los vendedores activos
            interasesor_data = interasesor_data[interasesor_data['Estado'].str.contains("Activado", na=False)]

            # Cruzar con los vendedores que tienen ventas
            vendedores_con_venta = interasesor_data[interasesor_data['Codigo'].isin(self.filtered_data_total['Código Vendedor'])]

            # Seleccionar y renombrar columnas requeridas
            vendedores_final = vendedores_con_venta[
                ['Codigo', 'Nombre', 'Direccion', 'Documento', 'Codigo supervisor']
            ].rename(columns={
                'Codigo': 'Código',
                'Nombre': 'Nombre',
                'Direccion': 'Ubicación',
                'Documento': 'Cédula',
                'Codigo supervisor': 'Código Supervisor'
            })
            
            # Ordenar por Código
            self.vendedores_final = vendedores_final.sort_values(by='Código')

            # Ruta para guardar el archivo txt
            output_txt = os.path.join(self.output_folder, 'Vendedores.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(self.vendedores_final.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in self.vendedores_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Vendedores': {e}")
            raise

    def generar_supervisores(self):
        """Genera los archivos 'Supervisores.txt' y 'Supervisores.xlsx' cruzando los datos con intersupervisor.txt."""
        try:
            # Ruta del archivo intersupervisor desde config
            intersupervisor_path = self.company_config['paths']['intersupervisor']
            
            # Verificar que el archivo exista
            self.verificar_archivo(intersupervisor_path)

            # Cargar los datos de intersupervisor.txt
            intersupervisor_data = pd.read_csv(
                intersupervisor_path,
                sep='{',
                engine='python',
                encoding='latin1',
                names=["Codigo", "Documento", "Nombre", "Apellido", "Telefono", "Direccion",
                       "Cargo", "Portafolio", "Estado", "Codigo bodega"]
            )

            # Filtrar solo los supervisores activos
            intersupervisor_data = intersupervisor_data[intersupervisor_data['Estado'].str.contains("Activado", na=False)]

            # Obtener los códigos de supervisor del archivo de vendedores
            supervisores_codigo = self.vendedores_final['Código Supervisor'].unique()

            # Filtrar los supervisores en base a los códigos de supervisor
            supervisores_final = intersupervisor_data[intersupervisor_data['Codigo'].isin(supervisores_codigo)]

            # Seleccionar y renombrar columnas requeridas
            supervisores_final = supervisores_final[['Codigo', 'Nombre']].rename(columns={
                'Codigo': 'Código',
                'Nombre': 'Nombre'
            })

            # Ordenar supervisores por 'Código'
            supervisores_final = supervisores_final.sort_values(by='Código')

            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'Supervisores.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(supervisores_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in supervisores_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Supervisores': {e}")
            raise

    def _normalizar_texto(self, texto):
        """Normaliza texto eliminando tildes y caracteres especiales para matching."""
        if pd.isna(texto):
            return ""
        texto = str(texto).strip()
        # Eliminar tildes
        texto = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        texto = texto.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        texto = texto.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
        texto = texto.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
        return texto

    def cargar_tipologia_negocio(self):
        """Carga la tipología de negocio desde PROVEE-TSOL.xlsx hoja TIPOLOGIA."""
        try:
            self.verificar_archivo(self.catalogo_principal)
            
            # Configuración de tipología desde config
            tip_config = self.company_config.get('tipologia_negocio', {})
            hoja = tip_config.get('hoja_excel', 'TIPOLOGIA')
            col_codigo = tip_config.get('columnas', {}).get('codigo', 'Cod. necesidad')
            col_descripcion = tip_config.get('columnas', {}).get('descripcion', 'Nom. necesidad')
            
            # Leer hoja TIPOLOGIA
            tipologia_df = pd.read_excel(self.catalogo_principal, sheet_name=hoja)
            
            # Normalizar códigos para matching (eliminar tildes)
            tipologia_df[col_codigo] = tipologia_df[col_codigo].apply(self._normalizar_texto)
            
            # Crear diccionario de tipología: código normalizado -> código original
            self.tipologia_map = dict(zip(
                tipologia_df[col_codigo],
                tipologia_df[col_codigo]
            ))
            
            logger.info(f"Tipología cargada: {len(self.tipologia_map)} registros desde {hoja}")
            return tipologia_df[[col_codigo, col_descripcion]]
            
        except Exception as e:
            logger.error(f"Error al cargar tipología de negocio: {e}")
            raise

    def generar_tipos_de_negocio(self):
        """Genera los archivos 'Tipos De Negocio.txt' desde PROVEE-TSOL TIPOLOGIA."""
        try:
            # Cargar tipología desde PROVEE-TSOL
            tip_config = self.company_config.get('tipologia_negocio', {})
            col_codigo = tip_config.get('columnas', {}).get('codigo', 'Cod. necesidad')
            col_descripcion = tip_config.get('columnas', {}).get('descripcion', 'Nom. necesidad')
            
            tipologia_df = self.cargar_tipologia_negocio()
            
            # Renombrar columnas para salida
            tipos_negocio = tipologia_df.rename(columns={
                col_codigo: 'Código',
                col_descripcion: 'Nombre'
            })

            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'Tipos De Negocio.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(tipos_negocio.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in tipos_negocio.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar los archivos 'Tipos De Negocio': {e}")
            raise

    def generar_sku_productos(self):
        """Genera los archivos 'SKU (Productos).txt' filtrando desde PROVEE-TSOL por proveedores."""
        try:
            self.verificar_archivo(self.catalogo_principal)
            
            # Configuración de productos desde config
            prod_config = self.company_config.get('filtros_productos', {})
            hoja = prod_config.get('hoja_excel', 'PRODUCTO')
            col_codigo = prod_config.get('columnas', {}).get('codigo', 'Codigo SAP')
            col_nombre = prod_config.get('columnas', {}).get('nombre', 'Nombre')
            col_barras = prod_config.get('columnas', {}).get('codigo_barras', 'Codigo de barras')
            col_proveedor = prod_config.get('columnas', {}).get('proveedor', 'Proveedor')
            
            # Cargar datos del catálogo principal
            productos_df = pd.read_excel(self.catalogo_principal, sheet_name=hoja)

            # Filtrar por proveedores si están definidos
            if self.proveedores:
                regex_pattern = '|'.join([re.escape(proveedor) for proveedor in self.proveedores])
                productos_df = productos_df[productos_df[col_proveedor].str.contains(regex_pattern, case=False, na=False)]
                logger.info(f"Productos filtrados por proveedores: {len(productos_df)} registros")

            # Seleccionar y renombrar columnas
            productos_final = productos_df[[col_codigo, col_nombre, col_barras]].copy()
            productos_final = productos_final.rename(columns={
                col_codigo: 'Código',
                col_nombre: 'Nombre',
                col_barras: 'Código De Barras'
            })

            # Convertir a texto y limpiar
            productos_final['Código'] = productos_final['Código'].astype(str).str.strip().str.split('.').str[0]
            productos_final['Código De Barras'] = productos_final['Código De Barras'].astype(str).str.strip()

            # Agregar las columnas estáticas
            productos_final['Tipo Referencia'] = 'RG'
            productos_final['Tipo De Unidad'] = 'UND'
            productos_final['Compañía'] = productos_final['Código De Barras']

            # Seleccionar y ordenar columnas
            productos_final = productos_final[[
                'Código', 'Nombre', 'Tipo Referencia', 'Tipo De Unidad', 'Código De Barras', 'Compañía'
            ]]

            # Asignar productos_final como la maestra SKU
            self.sku_maestra = productos_final

            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'SKU (Productos).txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(productos_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in productos_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar los archivos 'SKU (Productos)': {e}")
            raise

    def generar_clientes(self):
        """Genera los archivos 'Clientes.txt' cruzando datos con intercliente.txt y PROVEE-TSOL TIPOLOGIA."""
        try:
            # Rutas de los archivos desde config
            intercliente_path = self.company_config['paths']['intercliente']
            
            # Verificar archivos
            self.verificar_archivo(intercliente_path)
            self.verificar_archivo(self.catalogo_principal)

            # Limpiar el archivo de entrada antes de cargarlo con pandas
            cleaned_lines = []
            with open(intercliente_path, 'r', encoding='Windows-1252') as file:
                for line in file:
                    # Reemplazar comillas estándar y no estándar con expresión regular
                    cleaned_line = line.strip().strip('"').strip('"').strip('"').strip("'").strip('`')
                    cleaned_line = re.sub(r'^"|"$', '', cleaned_line).strip()
                    cleaned_lines.append(cleaned_line)

            # Crear un archivo temporal limpio
            temp_path = 'intercliente_cleaned_eje.txt'
            with open(temp_path, 'w', encoding='Windows-1252') as temp_file:
                temp_file.write("\n".join(cleaned_lines))

            # Cargar datos limpios con pandas
            intercliente_data = pd.read_csv(
                temp_path,
                sep='{',
                engine='python',
                encoding='Windows-1252',
                names=["Cod. Cliente", "Nom. Cliente", "Fecha Ingreso", "Nit", "Direccion",
                       "Telefono", "Representante Legal", "Codigo Municipio",
                       "Codigo Negocio", "Tipo Negocio", "Estracto", "Barrio"]
            )

            # Renombrar y limpiar columnas
            intercliente_data.rename(columns={
                "Cod. Cliente": "Código",
                "Nom. Cliente": "Nombre",
                "Direccion": "Dirección",
                "Estracto": "Estrato",
                "Codigo Municipio": "Código Municipio",
                "Telefono": "Teléfono"
            }, inplace=True)

            # Normalizar códigos
            intercliente_data['Código'] = (
                intercliente_data['Código']
                .astype(str)
                .str.strip()
                .str.replace('-', '999')
                .str.replace('"', '')
            )

            # Cargar tipología desde PROVEE-TSOL
            self.cargar_tipologia_negocio()

            # Normalizar códigos de clientes únicos del DataFrame de ventas
            clientes_unicos = (
                self.filtered_data_total['Código Cliente']
                .astype(str)
                .str.strip()
                .str.replace('-', '999')
                .unique()
            )

            # Filtrar clientes presentes en intercliente.txt
            intercliente_data['Código'] = intercliente_data['Código'].str.strip()
            clientes_final = intercliente_data[intercliente_data['Código'].isin(clientes_unicos)].copy()

            # Determinar Código Tipo Negocio desde columna 'Codigo Negocio' cruzando con tipología
            def tipo_negocio(codigo_negocio):
                codigo_negocio_norm = self._normalizar_texto(codigo_negocio)
                # Buscar en tipología map
                if codigo_negocio_norm in self.tipologia_map:
                    return self.tipologia_map[codigo_negocio_norm]
                # Default: devolver el código normalizado
                return codigo_negocio_norm

            clientes_final['Código Tipo Negocio'] = clientes_final['Codigo Negocio'].apply(tipo_negocio)

            # Agregar columnas adicionales
            clientes_final['Código Sector DANE'] = ''
            clientes_final['Nombre Sector DANE'] = ''
            clientes_final['Código Zona Venta'] = ''

            # Seleccionar y ordenar las columnas requeridas
            columnas_finales = [
                'Código', 'Nombre', 'Fecha Ingreso', 'Nit', 'Dirección', 'Teléfono',
                'Representante Legal', 'Código Municipio', 'Código Tipo Negocio',
                'Estrato', 'Barrio', 'Código Sector DANE', 'Nombre Sector DANE', 'Código Zona Venta'
            ]
            clientes_final = clientes_final[columnas_finales]

            self.clientes_final = clientes_final.copy()

            # Rutas para los archivos de salida
            output_path_txt = os.path.join(self.output_folder, 'Clientes.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(columnas_finales)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in clientes_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar los archivos de clientes: {e}")
            raise

    def generar_inventario(self):
        """Genera los archivos 'Inventario.txt' filtrando por productos de la maestra SKU y proveedores."""
        try:
            # Ruta del archivo Consolidado.xlsx desde config
            inventario_path = self.config['files']['inventario']
            
            # Verificar que ambos archivos existan
            self.verificar_archivo(inventario_path)

            # Cargar los datos del archivo de inventario
            inventario_data = pd.read_excel(inventario_path, sheet_name='Informe')

            # Filtrar por proveedores definidos
            if not self.proveedores:
                raise ValueError("No se encontraron proveedores para filtrar el inventario.")

            regex_pattern = '|'.join([re.escape(proveedor) for proveedor in self.proveedores])
            inventario_data = inventario_data[inventario_data['Proveedor'].str.contains(regex_pattern, case=False, na=False)]

            # Normalizar los códigos en inventario
            inventario_data['Codigo articulo'] = inventario_data['Codigo articulo'].astype(str).str.strip().str.split('.').str[0]

            # Filtrar los productos que están en la maestra SKU
            if hasattr(self, 'sku_maestra'):
                inventario_data = inventario_data[inventario_data['Codigo articulo'].isin(self.sku_maestra['Código'])]

            # Crear DataFrame con las columnas requeridas
            inventario_final = inventario_data[['Codigo articulo', 'Unidades']].rename(columns={
                'Codigo articulo': 'Código Producto',
                'Unidades': 'Cantidad'
            })
            
            # Agregar columnas adicionales
            inventario_final['Fecha'] = datetime.now().strftime('%Y/%m/%d')
            inventario_final['Unidad de Medida'] = 'UND'

            # Seleccionar el orden de columnas
            inventario_final = inventario_final[['Fecha', 'Código Producto', 'Cantidad', 'Unidad de Medida']]

            # Agrupar por código de producto y sumar las cantidades
            inventario_final = inventario_final.groupby(
                ['Fecha', 'Código Producto', 'Unidad de Medida'], as_index=False
            ).agg({'Cantidad': 'sum'})
            
            self.inventario_final = inventario_final.copy()

            # Rutas para guardar los archivos
            output_path_txt = os.path.join(self.output_folder, 'Inventario.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(inventario_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in inventario_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar los archivos de inventario: {e}")
            raise

    def generar_municipios(self):
        """Genera el archivo de Municipios en formato TXT."""
        try:
            # Ruta del archivo interciudad desde config
            interciudad_path = self.company_config['paths']['interciudad']
            
            # Verificar que el archivo exista
            self.verificar_archivo(interciudad_path)

            # Cargar los datos del archivo interciudad.txt
            interciudad_data = pd.read_csv(
                interciudad_path,
                sep='{',
                engine='python',
                encoding='latin1',
                names=["Código", "Nombre"]
            )

            # Extraer los municipios únicos del DataFrame de clientes
            municipios_clientes = self.clientes_final['Código Municipio'].dropna().unique()

            # Filtrar los municipios en interciudad que aparecen en el DataFrame de clientes
            municipios_final = interciudad_data[interciudad_data['Código'].isin(municipios_clientes)].drop_duplicates()

            # Ruta para guardar el archivo TXT
            output_txt = os.path.join(self.output_folder, 'Municipios.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(municipios_final.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in municipios_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Municipios': {e}")
            raise

    def generar_barrios(self):
        """Genera el archivo de Barrios en formato TXT."""
        try:
            # Asegurarse de que el DataFrame de clientes exista
            if not hasattr(self, 'clientes_final'):
                raise AttributeError("El DataFrame 'clientes_final' no está definido.")

            # Filtrar y crear los datos únicos de Barrios
            barrios_df = self.clientes_final[['Código Municipio', 'Barrio']].drop_duplicates()

            # Crear la columna de Código usando el mismo valor que Nombre
            barrios_df = barrios_df.rename(columns={'Barrio': 'Nombre'})
            barrios_df['Código'] = barrios_df['Nombre']

            # Ordenar por Código Municipio y Nombre
            barrios_df = barrios_df.sort_values(by=['Código Municipio', 'Nombre']).reset_index(drop=True)

            # Reorganizar las columnas
            barrios_df = barrios_df[['Código', 'Nombre', 'Código Municipio']]

            # Ruta para guardar el archivo TXT
            output_txt = os.path.join(self.output_folder, 'Barrios.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(barrios_df.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in barrios_df.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Barrios': {e}")
            raise

    def generar_rutas(self):
        """Genera el archivo 'Rutas' cruzando datos de ventas con un archivo de rutas existente."""
        try:
            # Ruta del archivo rutero desde config
            rutas_path = self.config['files']['rutero']
            
            # Verificar que el archivo exista
            self.verificar_archivo(rutas_path)
            
            # Cargar datos del archivo rutero
            rutas_df = pd.read_excel(rutas_path, sheet_name='Informe')

            # Asegurarse de que las columnas necesarias existan
            rutas_df = rutas_df.rename(columns={'Codigo': 'Código Cliente', 'Cod. Asesor': 'Código Vendedor'})
            
            # Cruzar datos con ventas
            rutas_data = pd.merge(
                self.filtered_data_total[['Código Cliente', 'Código Vendedor']],
                rutas_df[['Código Cliente', 'Código Vendedor']],
                on=['Código Cliente', 'Código Vendedor'],
                how='inner'
            ).drop_duplicates()

            # Agregar columnas requeridas
            rutas_data['Mes'] = int(self.mes)
            rutas_data['Dia Semana'] = 1
            rutas_data['Frecuencia'] = 4

            # Aplicar el reemplazo en el código del cliente
            rutas_data['Código Cliente'] = rutas_data['Código Cliente'].apply(lambda x: str(x).replace('-', '999'))

            # Guardar archivos
            output_path_txt = os.path.join(self.output_folder, 'Rutas.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(rutas_data.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in rutas_data.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Rutas': {e}")
            raise

    def validar_inconsistencias(self):
        """Valida las inconsistencias entre las maestras y genera un reporte."""
        try:
            inconsistencias = []

            # Validar códigos de clientes
            if hasattr(self, 'filtered_data_total') and hasattr(self, 'clientes_final'):
                clientes_ventas = set(self.filtered_data_total['Código Cliente'])
                clientes_maestra = set(self.clientes_final['Código'])
                clientes_faltantes = clientes_ventas - clientes_maestra
                if clientes_faltantes:
                    inconsistencias.append({
                        'Maestra': 'Clientes',
                        'Códigos faltantes': list(clientes_faltantes)
                    })
                    logger.warning(f"Códigos de clientes faltantes en la maestra: {clientes_faltantes}")

            # Validar códigos de productos (SKU)
            if hasattr(self, 'filtered_data_total') and hasattr(self, 'inventario_final'):
                productos_inventario = set(self.inventario_final['Código Producto'])
                if hasattr(self, 'sku_maestra'):
                    productos_maestra = set(self.sku_maestra['Código'])
                    productos_faltantes = productos_inventario - productos_maestra
                    if productos_faltantes:
                        inconsistencias.append({
                            'Maestra': 'SKU',
                            'Códigos faltantes': list(productos_faltantes)
                        })
                        logger.warning(f"Códigos de productos faltantes en la maestra SKU: {productos_faltantes}")

            # Generar reporte de inconsistencias
            if inconsistencias:
                report_df = pd.DataFrame(inconsistencias)
                output_path_excel = os.path.join(self.output_folder, 'Reporte de Inconsistencias.xlsx')
                report_df.to_excel(output_path_excel, index=False, sheet_name='Inconsistencias', engine='openpyxl')
                logger.info(f"Reporte de inconsistencias generado: {output_path_excel}")
            else:
                logger.info("No se encontraron inconsistencias.")

        except Exception as e:
            logger.error(f"Error al validar las inconsistencias: {e}")
            raise

    def comprimir_archivos(self):
        """
        Comprime todos los archivos TXT generados en un archivo ZIP con el formato requerido.
        Elimina los archivos TXT originales y guarda el ZIP en la carpeta 'historico'.
        """
        try:
            # Obtener la última fecha de venta reportada
            if hasattr(self, 'filtered_data_total') and not self.filtered_data_total.empty:
                if isinstance(self.filtered_data_total['Fecha'].iloc[0], str):
                    fechas = pd.to_datetime(self.filtered_data_total['Fecha'])
                    ultima_fecha = fechas.max()
                else:
                    ultima_fecha = self.filtered_data_total['Fecha'].max()
                    
                try:
                    if isinstance(ultima_fecha, str):
                        partes = ultima_fecha.split('/')
                        dia = int(partes[2])
                        mes = int(partes[1])
                        ano = int(partes[0])
                    else:
                        dia = ultima_fecha.day
                        mes = ultima_fecha.month
                        ano = ultima_fecha.year
                except Exception:
                    logger.warning("No se pudo determinar la última fecha de venta. Usando último día del mes.")
                    dia = calendar.monthrange(int(self.ano), int(self.mes))[1]
                    mes = int(self.mes)
                    ano = int(self.ano)
            else:
                dia = calendar.monthrange(int(self.ano), int(self.mes))[1]
                mes = int(self.mes)
                ano = int(self.ano)
                
            # Crear el nombre del archivo ZIP - formato: {CODIGO}_{ano}6{mes:02d}{dia:02d}.zip
            zip_filename = f"{self.company_config['codigo']}_{ano}6{mes:02d}{dia:02d}.zip"
            zip_path = os.path.join(self.output_folder, zip_filename)
            
            # Crear la carpeta de histórico si no existe
            historico_folder = os.path.join(self.output_folder, "historico")
            if not os.path.exists(historico_folder):
                os.makedirs(historico_folder)
                logger.info(f"Carpeta de histórico creada: {historico_folder}")
            
            # Crear el archivo ZIP solo con archivos TXT
            txt_files = []
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.output_folder):
                    for file in files:
                        if file.endswith('.txt') and 'historico' not in root:
                            file_path = os.path.join(root, file)
                            arcname = os.path.basename(file_path)
                            zipf.write(file_path, arcname)
                            txt_files.append(file_path)
                            logger.info(f"Archivo TXT añadido al ZIP: {file}")
            
            # Mover el ZIP a la carpeta de histórico
            historico_zip_path = os.path.join(historico_folder, zip_filename)
            shutil.move(zip_path, historico_zip_path)
            logger.info(f"Archivo ZIP movido a histórico: {historico_zip_path}")
            
            # Eliminar los archivos TXT originales
            for txt_file in txt_files:
                os.remove(txt_file)
                logger.info(f"Archivo TXT eliminado: {txt_file}")
            
            logger.info(f"Proceso de compresión completado. ZIP guardado en: {historico_zip_path}")
            return historico_zip_path
        
        except Exception as e:
            logger.error(f"Error al comprimir los archivos: {e}")
            raise

    def enviar_por_ftp(self, zip_path):
        """Envía el archivo ZIP a un servidor FTP usando configuración del company_config."""
        try:
            # Verificar si FTP está habilitado
            if not self.company_config.get('ftp_enabled', False):
                logger.info("FTP no habilitado para esta empresa.")
                return False
                
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"El archivo ZIP no existe: {zip_path}")
            
            # Obtener configuración FTP
            ftp_config = self.config.get('ftp', {})
            ftp_host = ftp_config.get('host', 'apps.grupobit.net')
            ftp_port = ftp_config.get('port', 21)
            
            company_ftp = self.company_config.get('ftp', {})
            ftp_user = company_ftp.get('user')
            ftp_pass = company_ftp.get('password')
            
            if not ftp_user or not ftp_pass:
                logger.warning("Credenciales FTP no configuradas")
                return False
            
            print(f"Conectando al servidor FTP: {ftp_host}:{ftp_port}")
            logger.info(f"Conectando al servidor FTP: {ftp_host}:{ftp_port}")
            
            # Crear conexión FTP
            ftp = ftplib.FTP()
            ftp.connect(ftp_host, ftp_port, timeout=30)
            print(f"Conexión establecida con {ftp_host}")
            
            # Login
            print(f"Iniciando sesión como: {ftp_user}")
            ftp.login(ftp_user, ftp_pass)
            print(f"Sesión iniciada correctamente")
            
            # Subir archivo
            print(f"Subiendo archivo: {os.path.basename(zip_path)} ({os.path.getsize(zip_path)/1024/1024:.2f} MB)")
            with open(zip_path, 'rb') as file:
                remote_filename = os.path.basename(zip_path)
                ftp.storbinary(f'STOR {remote_filename}', file, blocksize=262144)
            
            print("Archivo subido correctamente")
            logger.info("Archivo subido correctamente")
            
            # Cerrar conexión
            ftp.quit()
            print("Conexión FTP cerrada")
            return True
            
        except Exception as e:
            print(f"Error en la transferencia FTP: {e}")
            logger.error(f"Error al enviar el archivo por FTP: {e}")
            return False

# Ejecución del script
if __name__ == '__main__':
    config_path = 'config.json'

    processor = VentaProcessor(config_path)

    # Cargar y filtrar los datos
    processor.cargar_y_filtrar_datos_por_periodo()

    # Procesar los datos
    processor.procesar_datos()

    # Guardar los resultados
    processor.guardar_archivo_ventas()
    processor.generar_listado_facturas()
    processor.generar_totales_de_control()
    processor.generar_vendedores()
    processor.generar_supervisores()
    processor.generar_tipos_de_negocio()
    processor.generar_sku_productos()
    processor.generar_clientes()
    processor.generar_municipios()
    processor.generar_inventario()
    processor.generar_barrios()
    processor.generar_rutas()
    processor.validar_inconsistencias()
    
    # Comprimir archivos
    zip_path = processor.comprimir_archivos()
    print(f"Archivos TXT comprimidos y guardados en: {zip_path}")
    
    # Enviar por FTP
    if processor.enviar_por_ftp(zip_path):
        print(f"Archivo enviado exitosamente al servidor FTP")
    else:
        print("No se envió el archivo por FTP (deshabilitado o error)")
