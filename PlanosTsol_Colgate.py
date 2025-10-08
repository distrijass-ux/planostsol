#PlanosTosl_Colgate.py
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
    filename='ventas_processor.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

class VentaProcessor:
    def __init__(self, config_path):
        self.config = self._cargar_configuracion(config_path)
        self.ventas_path = self.config.get('ventas_path')
        self.output_folder = self.config.get('output_folder', 'output_files')
        self.proveedores_file = self.config.get('proveedores_file')        # mes y ano se determinarán dinámicamente desde los datos del Excel
        self.mes = None
        self.ano = None
        self.proveedores = []
        self.filtered_data = None
        self._crear_carpeta_salida()
        if self.proveedores_file:
            self._cargar_proveedores()

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

    def _cargar_proveedores(self):
        """Carga la lista de proveedores desde un archivo de texto."""
        if not os.path.isfile(self.proveedores_file):
            logger.error(f"Archivo de proveedores no encontrado: {self.proveedores_file}")
            raise FileNotFoundError(f"Archivo de proveedores no encontrado: {self.proveedores_file}")
        try:
            with open(self.proveedores_file, 'r', encoding='utf-8') as file:
                self.proveedores = [line.strip() for line in file.readlines() if line.strip()]
            if not self.proveedores:
                logger.warning("El archivo de proveedores está vacío.")
            logger.info(f"Proveedores cargados: {self.proveedores}")
        except Exception as e:
            logger.error(f"Error al cargar la lista de proveedores: {e}")
            raise

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
            # Ruta para el archivo Excel
            output_path_excel = os.path.join(self.output_folder, 'ventas.xlsx')

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

            # Guardar el archivo Excel
            # excel_data = self.filtered_data.copy()
            # excel_data.to_excel(output_path_excel, index=False, sheet_name='Ventas', engine='openpyxl')
            # logger.info(f"Archivo Excel guardado exitosamente en: {output_path_excel}")

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
                Valor_Facturado_Casa_Comercial = ('Valor Total Item Vendido', 'sum')
            ).reset_index()

            # Convertir valores a formato con dos decimales
            facturas_resumen['Valor_Total_Factura'] = facturas_resumen['Valor_Total_Factura'].round(2)
            facturas_resumen['Valor_Facturado_Casa_Comercial'] = facturas_resumen['Valor_Facturado_Casa_Comercial'].round(2)

            # Ruta para los archivos de salida
            output_txt = os.path.join(self.output_folder, 'Listado de Facturas.txt')
            output_excel = os.path.join(self.output_folder, 'Listado de Facturas.xlsx')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(facturas_resumen.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in facturas_resumen.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

            # Guardar archivo Excel
            # facturas_resumen.to_excel(output_excel, index=False, sheet_name='Listado Facturas', engine='openpyxl')
            # logger.info(f"Archivo Excel generado: {output_excel}")

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
            output_excel = os.path.join(self.output_folder, 'Totales de Control.xlsx')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(totales_control.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in totales_control.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

            # Guardar archivo Excel
            # totales_control.to_excel(output_excel, index=False, sheet_name='Totales de Control', engine='openpyxl')
            # logger.info(f"Archivo Excel generado: {output_excel}")

        except Exception as e:
            logger.error(f"Error al generar los totales de control: {e}")
            raise

    def generar_vendedores(self):
        """Genera el archivo 'Vendedores' cruzando los datos de ventas con interasesor.txt."""
        try:
            # Ruta del archivo interasesor
            interasesor_path = self.config.get('interasesor_path', 'interasesor.txt')
            
            # Verificar que el archivo exista
            self.verificar_archivo(interasesor_path)

            # Cargar los datos de interasesor.txt
            interasesor_data = pd.read_csv(
                interasesor_path,
                sep='{',
                engine='python',
                encoding='latin1',  # Codificación alternativa para evitar errores
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

            # Ruta para guardar el archivo de excel
            output_path = os.path.join(self.output_folder, 'Vendedores.xlsx')
            
            # Ruta para guardar el archivo txt
            output_txt = os.path.join(self.output_folder, 'Vendedores.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(self.vendedores_final.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in self.vendedores_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

            # Guardar archivo Excel
            # self.vendedores_final.to_excel(output_path, index=False, sheet_name='Vendedores', engine='openpyxl')
            # logger.info(f"Archivo 'Vendedores' generado exitosamente en: {output_path}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Vendedores': {e}")
            raise

    def generar_supervisores(self):
        """Genera los archivos 'Supervisores.txt' y 'Supervisores.xlsx' cruzando los datos con intersupervisor.txt."""
        try:
            # Ruta del archivo intersupervisor
            intersupervisor_path = self.config.get('intersupervisor_path', 'intersupervisor.txt')
            
            # Verificar que el archivo exista
            self.verificar_archivo(intersupervisor_path)

            # Cargar los datos de intersupervisor.txt
            intersupervisor_data = pd.read_csv(
                intersupervisor_path,
                sep='{',
                engine='python',
                encoding='latin1',  # Codificación alternativa para evitar errores
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

            # Ruta para guardar el archivo de Excel
            output_path_excel = os.path.join(self.output_folder, 'Supervisores.xlsx')
            
            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'Supervisores.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(supervisores_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in supervisores_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # supervisores_final.to_excel(output_path_excel, index=False, sheet_name='Supervisores', engine='openpyxl')
            # logger.info(f"Archivo 'Supervisores' generado exitosamente en: {output_path_excel}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Supervisores': {e}")
            raise

    def generar_tipos_de_negocio(self):
        """Genera los archivos 'Tipos De Negocio.txt' y 'Tipos De Negocio.xlsx' con los tipos TE, TT, MM y SN."""
        try:
            # Definir los datos estáticos, ahora incluyendo MM y SN
            tipos_negocio = pd.DataFrame({
                'Código': ['TE', 'TT', 'MM', 'SN'],
                'Nombre': ['Tienda Especializada', 'Tienda a Tienda', 'Minimercado', 'Sin Tipología']
            })

            # Ruta para guardar el archivo Excel
            output_path_excel = os.path.join(self.output_folder, 'Tipos De Negocio.xlsx')
            
            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'Tipos De Negocio.txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(tipos_negocio.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in tipos_negocio.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # tipos_negocio.to_excel(output_path_excel, index=False, sheet_name='Tipos De Negocio', engine='openpyxl')
            # logger.info(f"Archivo 'Tipos De Negocio' generado exitosamente en: {output_path_excel}")

        except Exception as e:
            logger.error(f"Error al generar los archivos 'Tipos De Negocio': {e}")
            raise

    def generar_sku_productos(self):
        """Genera los archivos 'SKU (Productos).txt' y 'SKU (Productos).xlsx' filtrando por longitud de código y prefijo '23'."""
        try:
            # Ruta del archivo de productos
            productos_path = self.config.get('colgate_path', r'D://Distrijass//Sistema Info//Información//Colgate//023-COLGATE PALMOLIVE.xlsx')
            
            # Verificar que el archivo exista
            self.verificar_archivo(productos_path)
            
            # Cargar los datos del archivo de productos
            productos_data = pd.ExcelFile(productos_path)
            productos_df = productos_data.parse('Productos EQ')

            # Filtrar las columnas necesarias
            productos_df = productos_df[['Pro_Cod', 'Producto', 'ALTERNO']].rename(columns={
                'Pro_Cod': 'Código',
                'Producto': 'Nombre',
                'ALTERNO': 'Código De Barras'
            })

            # Convertir las columnas relevantes a texto y limpiar los datos
            productos_df['Código'] = productos_df['Código'].astype(str).str.strip().str.split('.').str[0]
            productos_df['Código De Barras'] = productos_df['Código De Barras'].astype(str).str.strip()

            # Filtrar los productos según las nuevas restricciones
            productos_final = productos_df[
                (productos_df['Código'].str.len() <= 5) &  # Máximo 5 caracteres
                (productos_df['Código'].str[:2] == '23')  # Empieza con "23"
            ].copy()

            # Agregar las columnas estáticas
            productos_final.loc[:, 'Tipo Referencia'] = 'RG'
            productos_final.loc[:, 'Tipo De Unidad'] = 'UND'
            productos_final.loc[:, 'Compañía'] = productos_final['Código De Barras']

            # Seleccionar y ordenar columnas
            productos_final = productos_final[[
                'Código', 'Nombre', 'Tipo Referencia', 'Tipo De Unidad', 'Código De Barras', 'Compañía'
            ]]

            # Asignar productos_final como la maestra SKU
            self.sku_maestra = productos_final

            # Ruta para guardar el archivo Excel
            output_path_excel = os.path.join(self.output_folder, 'SKU (Productos).xlsx')
            
            # Ruta para guardar el archivo TXT
            output_path_txt = os.path.join(self.output_folder, 'SKU (Productos).txt')
            
            # Guardar archivo TXT
            encabezado_txt = '{'.join(productos_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in productos_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # productos_final.to_excel(output_path_excel, index=False, sheet_name='SKU (Productos)', engine='openpyxl')
            # logger.info(f"Archivo 'SKU (Productos)' generado exitosamente en: {output_path_excel}")

        except Exception as e:
            logger.error(f"Error al generar los archivos 'SKU (Productos)': {e}")
            raise


    def generar_clientes(self):
        """Genera los archivos 'Clientes.txt' y 'Clientes.xlsx' cruzando datos con intercliente.txt y TE Viejos."""
        try:
            # Rutas de los archivos
            intercliente_path = self.config.get(
                'intercliente_path',
                r'D:\Distrijass\Sistema Info\Información\Envío TSOL\TSOL\Distrijass\intercliente.txt'
            )
            colgate_path = self.config.get(
                'colgate_path',
                r'D:\Distrijass\Sistema Info\Información\Colgate\023-COLGATE PALMOLIVE.xlsx'
            )

            # Verificar archivos
            self.verificar_archivo(intercliente_path)
            self.verificar_archivo(colgate_path)

            # Limpiar el archivo de entrada antes de cargarlo con pandas
            cleaned_lines = []
            with open(intercliente_path, 'r', encoding='Windows-1252') as file:
                for line in file:
                    # Reemplazar comillas estándar y no estándar con expresión regular
                    cleaned_line = line.strip().strip('"').strip('“').strip('”').strip("'").strip('`')
                    cleaned_line = re.sub(r'^"|"$', '', cleaned_line).strip()
                    cleaned_lines.append(cleaned_line)

            # Crear un archivo temporal limpio
            temp_path = 'intercliente_cleaned.txt'
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
            )
            # Normalizar códigos
            intercliente_data['Código'] = (
                intercliente_data['Código']
                .astype(str)
                .str.strip()
                .str.replace('"', '')
            )

            # Cargar TE Viejos de Colgate
            colgate_data = pd.ExcelFile(colgate_path)
            te_viejos = colgate_data.parse('TE Viejos')
            te_viejos['CLIENTES'] = te_viejos['CLIENTES'].astype(str).str.strip()

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

            # Cargar archivo mm.xlsx y obtener los clientes por tipología (MM o SN)
            mm_path = self.config.get('mm_path', 'mm.xlsx')
            clientes_mm_mm = set()
            clientes_mm_sn = set()
            if os.path.isfile(mm_path):
                mm_df = pd.read_excel(mm_path, dtype={'Cod. cliente': str})
                # Detectar nombre de la columna de tipología de forma flexible
                tipologia_col = None
                for col in mm_df.columns:
                    col_norm = str(col).strip().lower()
                    if col_norm in {'tipologia', 'tipología', 'tipo', 'tipo_negocio', 'tipologia mm/sn', 'mm_sn'}:
                        tipologia_col = col
                        break
                # Normalizar código y tipología
                mm_df['Cod. cliente'] = (
                    mm_df['Cod. cliente'].astype(str).str.strip()
                    .str.replace('-', '999').str.replace('"', '').str.replace("'", '')
                )
                if tipologia_col is not None:
                    mm_df['__TIPOLOGIA__'] = mm_df[tipologia_col].astype(str).str.strip().str.upper()
                    clientes_mm_mm = set(mm_df.loc[mm_df['__TIPOLOGIA__'] == 'MM', 'Cod. cliente'])
                    clientes_mm_sn = set(mm_df.loc[mm_df['__TIPOLOGIA__'] == 'SN', 'Cod. cliente'])
                else:
                    # Compatibilidad hacia atrás: si no hay columna de tipología, todo es MM
                    clientes_mm_mm = set(mm_df['Cod. cliente'])
                print(f"MM.xlsx -> MM: {len(clientes_mm_mm)}, SN: {len(clientes_mm_sn)}")
            
            # Determinar Código Tipo Negocio con prioridad MM > SN > TE > TT
            te_viejos_clientes = (
                te_viejos['CLIENTES']
                .astype(str)
                .str.strip()
                .str.replace('-', '999')
                .str.replace('"', '')
                .str.replace("'", '')
                .values
            )
            def tipo_negocio(codigo):
                codigo = str(codigo).strip().replace('-', '999').replace('"', '').replace("'", '')
                if codigo in clientes_mm_mm:
                    return 'MM'
                elif codigo in clientes_mm_sn:
                    return 'SN'
                elif codigo in te_viejos_clientes:
                    return 'TE'
                else:
                    return 'TT'

            clientes_final['Código Tipo Negocio'] = clientes_final['Código'].apply(tipo_negocio)

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
            output_path_excel = os.path.join(self.output_folder, 'Clientes.xlsx')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(columnas_finales)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in clientes_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # clientes_final.to_excel(output_path_excel, index=False, sheet_name='Clientes', engine='openpyxl')
            # logger.info(f"Archivo 'Clientes' generado exitosamente en: {output_path_excel}")

        except Exception as e:
            logger.error(f"Error al generar los archivos de clientes: {e}")
            raise




    def generar_inventario(self):
        """Genera los archivos 'Inventario.txt' y 'Inventario.xlsx' filtrando por productos de 'Productos EQ' y proveedores."""
        try:
            # Ruta del archivo Consolidado.xlsx
            inventario_path = self.config.get(
                'inventario_path',
                r'D:\Distrijass\Sistema Info\Información\Inventarios\Cierres consolidados Inv 2025\Consolidado 2025-01.xlsx'
            )
            productos_path = self.config.get(
                'colgate_path',
                r'D://Distrijass//Sistema Info//Información//Colgate//023-COLGATE PALMOLIVE.xlsx'
            )
            
            # Verificar que ambos archivos existan
            self.verificar_archivo(inventario_path)
            self.verificar_archivo(productos_path)

            # Cargar los datos del archivo de inventario
            inventario_data = pd.read_excel(inventario_path, sheet_name='Informe')

            # Cargar los datos del archivo de productos
            productos_data = pd.ExcelFile(productos_path)
            productos_df = productos_data.parse('Productos EQ')

            # Filtrar las columnas necesarias de productos
            productos_df = productos_df[['Pro_Cod']].rename(columns={'Pro_Cod': 'Código Producto'})
            productos_df['Código Producto'] = productos_df['Código Producto'].astype(str).str.strip().str.split('.').str[0]

            # Filtrar por proveedores definidos
            if not self.proveedores:
                raise ValueError("No se encontraron proveedores para filtrar el inventario.")

            regex_pattern = '|'.join([re.escape(proveedor) for proveedor in self.proveedores])
            inventario_data = inventario_data[inventario_data['Proveedor'].str.contains(regex_pattern, case=False, na=False)]

            # Normalizar los códigos en inventario
            inventario_data['Codigo articulo'] = inventario_data['Codigo articulo'].astype(str).str.strip().str.split('.').str[0]

            # Filtrar los productos que están en Productos EQ
            inventario_data = inventario_data[inventario_data['Codigo articulo'].isin(productos_df['Código Producto'])]

            # Crear DataFrame con las columnas requeridas
            inventario_final = inventario_data[['Codigo articulo', 'Unidades']].rename(columns={
                'Codigo articulo': 'Código Producto',
                'Unidades': 'Cantidad'
            })
            
            # Agregar columnas adicionales
            inventario_final['Fecha'] = datetime.now().strftime('%Y/%m/%d')  # Fecha actual
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
            output_path_excel = os.path.join(self.output_folder, 'Inventario.xlsx')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(inventario_final.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in inventario_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # inventario_final.to_excel(output_path_excel, index=False, sheet_name='Inventario', engine='openpyxl')
            # logger.info(f"Archivo 'Inventario' generado exitosamente en: {output_path_excel}")

        except Exception as e:
            logger.error(f"Error al generar los archivos de inventario: {e}")
            raise



    def generar_municipios(self):
        """Genera el archivo de Municipios en formato TXT y Excel."""
        try:
            # Ruta del archivo interciudad
            interciudad_path = self.config.get('interciudad_path', 'interciudad.txt')
            
            # Verificar que el archivo exista
            self.verificar_archivo(interciudad_path)

            # Cargar los datos del archivo interciudad.txt
            interciudad_data = pd.read_csv(
                interciudad_path,
                sep='{',
                engine='python',
                encoding='latin1',  # Codificación alternativa para evitar errores
                names=["Código", "Nombre"]
            )

            # Extraer los municipios únicos del DataFrame de clientes
            municipios_clientes = self.clientes_final['Código Municipio'].dropna().unique()

            # Filtrar los municipios en interciudad que aparecen en el DataFrame de clientes
            municipios_final = interciudad_data[interciudad_data['Código'].isin(municipios_clientes)].drop_duplicates()

            # Ruta para guardar el archivo de Excel
            output_excel = os.path.join(self.output_folder, 'Municipios.xlsx')

            # Ruta para guardar el archivo TXT
            output_txt = os.path.join(self.output_folder, 'Municipios.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(municipios_final.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in municipios_final.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

            # Guardar archivo Excel
            # municipios_final.to_excel(output_excel, index=False, sheet_name='Municipios', engine='openpyxl')
            # logger.info(f"Archivo Excel generado: {output_excel}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Municipios': {e}")
            raise

    def generar_barrios(self):
        """Genera el archivo de Barrios en formato TXT y Excel."""
        try:
            # Asegurarse de que el DataFrame de clientes exista
            if not hasattr(self, 'clientes_final'):
                raise AttributeError("El DataFrame 'clientes_final' no está definido. Asegúrate de ejecutar el método correspondiente.")

            # Filtrar y crear los datos únicos de Barrios
            barrios_df = self.clientes_final[['Código Municipio', 'Barrio']].drop_duplicates()

            # Crear la columna de Código usando el mismo valor que Nombre
            barrios_df = barrios_df.rename(columns={'Barrio': 'Nombre'})
            barrios_df['Código'] = barrios_df['Nombre']

            # Ordenar por Código Municipio y Nombre
            barrios_df = barrios_df.sort_values(by=['Código Municipio', 'Nombre']).reset_index(drop=True)

            # Reorganizar las columnas
            barrios_df = barrios_df[['Código', 'Nombre', 'Código Municipio']]

            # Ruta para guardar el archivo de Excel
            output_excel = os.path.join(self.output_folder, 'Barrios.xlsx')

            # Ruta para guardar el archivo TXT
            output_txt = os.path.join(self.output_folder, 'Barrios.txt')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(barrios_df.columns)
            with open(output_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in barrios_df.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_txt}")

            # Guardar archivo Excel
            # barrios_df.to_excel(output_excel, index=False, sheet_name='Barrios', engine='openpyxl')
            # logger.info(f"Archivo Excel generado: {output_excel}")

        except Exception as e:
            logger.error(f"Error al generar el archivo 'Barrios': {e}")
            raise

    def generar_rutas(self):
        """Genera el archivo 'Rutas' cruzando datos de ventas con un archivo de rutas existente."""
        try:
            # Ruta del archivo rutero
            rutas_path = self.config.get('rutero_path', r'D://Distrijass//Sistema Info//Información//Ruteros//ruterojass.xlsx')
            
            # Verificar que el archivo exista
            self.verificar_archivo(rutas_path)
            
            # Cargar datos del archivo rutero
            rutas_df = pd.read_excel(rutas_path, sheet_name='Informe')

            # Asegurarse de que las columnas necesarias existan
            rutas_df = rutas_df.rename(columns={'Codigo': 'Código Cliente', 'Cod. Asesor': 'Código Vendedor'})
            self.filtered_data_total = self.filtered_data_total.rename(columns={'Cod. Cliente': 'Código Cliente', 'Cod. Vendedor': 'Código Vendedor'})

            # Verificar columnas
            logger.debug(f"Columnas en self.filtered_data_total: {self.filtered_data_total.columns}")
            logger.debug(f"Columnas en rutas_df: {rutas_df.columns}")

            # Cruzar datos con ventas
            rutas_data = pd.merge(
                self.filtered_data_total[['Código Cliente', 'Código Vendedor']],
                rutas_df[['Código Cliente', 'Código Vendedor']],
                on=['Código Cliente', 'Código Vendedor'],
                how='inner'
            ).drop_duplicates()

            # Agregar columnas requeridas
            rutas_data['Mes'] = int(self.mes)
            rutas_data['Dia Semana'] = 1  # Ajustar según el día real si es necesario
            rutas_data['Frecuencia'] = 4

            # Aplicar el reemplazo en el código del cliente
            rutas_data['Código Cliente'] = rutas_data['Código Cliente'].apply(lambda x: str(x).replace('-', '999'))

            # Guardar archivos
            output_path_txt = os.path.join(self.output_folder, 'Rutas.txt')
            output_path_excel = os.path.join(self.output_folder, 'Rutas.xlsx')

            # Guardar archivo TXT
            encabezado_txt = '{'.join(rutas_data.columns)
            with open(output_path_txt, 'w', encoding='utf-8') as txt_file:
                txt_file.write(encabezado_txt + '\n')
                for _, row in rutas_data.iterrows():
                    txt_file.write('{'.join(map(str, row)) + '\n')
            logger.info(f"Archivo TXT generado: {output_path_txt}")

            # Guardar archivo Excel
            # rutas_data.to_excel(output_path_excel, index=False, sheet_name='Rutas', engine='openpyxl')
            # logger.info(f"Archivo 'Rutas' generado exitosamente en: {output_path_excel}")

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
            if hasattr(self, 'filtered_data_total'):
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
                # Crear un DataFrame con las inconsistencias
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
        Utiliza la fecha del último día de venta reportado para el nombre del archivo.
        """
        
        try:
            # Obtener la última fecha de venta reportada
            if hasattr(self, 'filtered_data_total') and not self.filtered_data_total.empty:
                # Verificar si la fecha ya está en formato string o es datetime
                if isinstance(self.filtered_data_total['Fecha'].iloc[0], str):
                    # Convertir de string a datetime para poder encontrar el máximo
                    fechas = pd.to_datetime(self.filtered_data_total['Fecha'])
                    ultima_fecha = fechas.max()
                else:
                    # Si es datetime, simplemente encontrar el máximo
                    ultima_fecha = self.filtered_data_total['Fecha'].max()
                    
                # Extraer día, mes y año de la última fecha
                try:
                    if isinstance(ultima_fecha, str):
                        # Si es string en formato 'YYYY/MM/DD'
                        partes = ultima_fecha.split('/')
                        dia = int(partes[2])
                        mes = int(partes[1])
                        ano = int(partes[0])
                    else:
                        # Si es datetime
                        dia = ultima_fecha.day
                        mes = ultima_fecha.month
                        ano = ultima_fecha.year
                except Exception:
                    # En caso de error, usar el último día del mes como fallback
                    logger.warning("No se pudo determinar la última fecha de venta. Usando último día del mes.")
                    dia = calendar.monthrange(int(self.ano), int(self.mes))[1]
                    mes = int(self.mes)
                    ano = int(self.ano)
            else:
                # Si no hay datos de ventas, usar el último día del mes
                dia = calendar.monthrange(int(self.ano), int(self.mes))[1]
                mes = int(self.mes)
                ano = int(self.ano)
                
            # Crear el formato de fecha para el nombre del archivo
            fecha = f"{dia:02d}{mes:02d}{ano}"
            
            # Crear el nombre del archivo ZIP
            zip_filename = f"COLGATE_214330_{ano}6{mes:02d}{dia:02d}.zip"
            zip_path = os.path.join(self.output_folder, zip_filename)
            
            # Resto del método se mantiene igual...
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
                        # Solo incluir archivos TXT y excluir la carpeta histórico
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

    def enviar_por_ftp(self, zip_path, ftp_host, ftp_port, ftp_user=None, ftp_pass=None):
        """Envía el archivo ZIP a un servidor FTP usando la configuración probada."""
        try:
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"El archivo ZIP no existe: {zip_path}")
            
            print(f"Conectando al servidor FTP: {ftp_host}:{ftp_port}")
            logger.info(f"Conectando al servidor FTP: {ftp_host}:{ftp_port}")
            
            # Crear conexión FTP
            ftp = ftplib.FTP()
            ftp.connect(ftp_host, ftp_port, timeout=30)
            print(f"Conexión establecida con {ftp_host}")
            logger.info(f"Conexión establecida con {ftp_host}")
            
            # Login
            print(f"Iniciando sesión como: {ftp_user}")
            logger.info(f"Iniciando sesión como: {ftp_user}")
            ftp.login(ftp_user, ftp_pass)
            print(f"Sesión iniciada correctamente - Directorio actual: {ftp.pwd()}")
            
            # Subir archivo
            print(f"Subiendo archivo: {os.path.basename(zip_path)} ({os.path.getsize(zip_path)/1024/1024:.2f} MB)")
            logger.info(f"Subiendo archivo: {os.path.basename(zip_path)} ({os.path.getsize(zip_path)/1024/1024:.2f} MB)")
            with open(zip_path, 'rb') as file:
                remote_filename = os.path.basename(zip_path)
                ftp.storbinary(f'STOR {remote_filename}', file, blocksize=262144)
            
            print("Archivo subido correctamente")
            logger.info("Archivo subido correctamente")
            
            # Verificar que el archivo se subió
            print("Verificando archivos en el servidor:")
            logger.info("Verificando archivos en el servidor:")
            files = []
            ftp.dir(files.append)
            for file_info in files:
                print(f"  {file_info}")
            
            # Cerrar conexión
            ftp.quit()
            print("Conexión FTP cerrada")
            logger.info("Conexión FTP cerrada")
            return True
            
        except Exception as e:
            print(f"Error en la transferencia FTP: {e.__class__.__name__}: {e}")
            logger.error(f"Error al enviar el archivo por FTP: {e}")
            raise

    # Ejecución del script
if __name__ == '__main__':
    config_path = 'config.json'  # Ruta del archivo de configuración

    processor = VentaProcessor(config_path)

    # Cargar y filtrar los datos
    processor.cargar_y_filtrar_datos_por_periodo()

    # Procesar los datos
    processor.procesar_datos()

    # Guardar los resultados
    processor.guardar_archivo_ventas()
    
    # Generar el listado de facturas
    processor.generar_listado_facturas()
    
    # Generar los totales de control
    processor.generar_totales_de_control()
    
    # Generar el archivo de vendedores
    processor.generar_vendedores()

    # Generar el archivo de supervisores
    processor.generar_supervisores()
    
    # Generar el archivo de Tipos De Negocio
    processor.generar_tipos_de_negocio()
    
    # Generar el archivo SKU (Productos)
    processor.generar_sku_productos()
    
    # Generar los archivos de clientes
    processor.generar_clientes()
    
    # Generar el archivo de municipios
    processor.generar_municipios()
    
    # Generar el archivo de inventario
    processor.generar_inventario()
    
    # Generar el archivo de barrios
    processor.generar_barrios()
    
    # Generar rutas
    processor.generar_rutas()
    
    # Validar inconsistencias
    processor.validar_inconsistencias()
    
    # Comprimir archivos
    zip_path = processor.comprimir_archivos()
    
    print(f"Archivos TXT comprimidos en ZIP y guardado en: {zip_path}")
    
    # Obtener credenciales FTP del archivo de configuración
    try:
        ftp_host = processor.config.get('ftp_host', 'apps.grupobit.net')
        ftp_port = processor.config.get('ftp_port', 21)
        ftp_user = processor.config.get('ftp_user')
        ftp_pass = processor.config.get('ftp_pass')
        
        print(f"Intentando enviar archivo al servidor FTP: {ftp_host}:{ftp_port}")
        print(f"Usuario: {ftp_user}")
        
        # Enviar por FTP si se proporcionaron credenciales
        if ftp_user and ftp_pass:
            try:
                if processor.enviar_por_ftp(zip_path, ftp_host, ftp_port, ftp_user, ftp_pass):
                    print(f"Archivo enviado exitosamente al servidor FTP: {ftp_host}")
            except Exception as e:
                print(f"Error al enviar por FTP: {e}")
                print("Verificando conectividad de red...")
                
                # Diagnostics check
                import socket
                try:
                    # Try to connect to a well-known internet host (Google's DNS)
                    socket.create_connection(("8.8.8.8", 53), timeout=5)
                    print("Conectividad a Internet: OK")
                except OSError:
                    print("⚠️ ALERTA: No hay conectividad a Internet")
                    
                print("\nPosibles soluciones:")
                print("1. Verifique su conexión a Internet")
                print("2. Verifique que el servidor FTP esté disponible") 
                print("3. Confirme que el nombre del servidor es correcto: apps.grupobit.net")
                print("4. Pruebe usando la dirección IP directa en lugar del nombre de host")
                print("5. Verifique que su firewall no esté bloqueando conexiones FTP")
        else:
            print("No se pudieron enviar los archivos por FTP: credenciales no proporcionadas.")
            print("Por favor añada 'ftp_user' y 'ftp_pass' en su archivo de configuración.")
    except Exception as e:
        print(f"Error al enviar por FTP: {e}")
