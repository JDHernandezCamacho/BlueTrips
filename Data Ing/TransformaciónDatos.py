# Se importa Pandas para la transformación de datos
import pandas as pd
import os 
import mysql.connector
from mysql.connector import errorcode



# Se transforman los CSVs en DataFrames
Calidad_Aire = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/Datos_Calidad_Aire.csv')
Alternative_Fuel_Vehicles = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/Alternative Fuel Vehicles US.csv')
ElectricCarData_Norm = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/ElectricCarData_Norm.csv')
ElectricCarData_Clean = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/ElectricCarData_Clean.csv')
Light_Duty_Vehicles = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/Light Duty Vehicles.csv')
Vehicle_Fuel_Economy = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/Vehicle Fuel Economy Data.csv')
Taxi_zone_lookup = pd.read_csv('C:/Users/dispe/OneDrive/Documentos/CLASES/Datos Extraídos/Taxi+_zone_lookup.csv')




# Se crea la clase "ETLProcceso"
class ETLProcessor:
    
    # Método constructor de la clase. Inicializa las propiedades del objeto.
    def __init__(self, df, nombre):
        
        self.df = df # Asigna el DataFrame pasado como argumento a una propiedad del objeto.
        self.nombre = nombre  # Asigna el nombre pasado como argumento a una propiedad del objeto.
    
    
    # Método para manejar los valores nulos en el DataFrame.
    def ManejoValoresNulos(self):
        
        columnas_numericas = self.df.select_dtypes(include = ['number']).columns        # Selecciona las columnas numéricas del DataFrame.
        self.df[columnas_numericas] = self.df[columnas_numericas].fillna(0)     # Rellena los valores nulos de las columnas numéricas con 0.
            
        columnas_texto = self.df.select_dtypes(include = ['object']).columns       # Selecciona las columnas de tipo texto del DataFrame. 
        self.df[columnas_texto] = self.df[columnas_texto].fillna('Sin Dato')    # Rellena los valores nulos de las columnas de texto con 'Sin Dato'.
        
    
    # Método para manejar los tipos de datos en el DataFrame.
    def ManejoTiposDatos(self):
        
        for column in self.df.columns:  # Itera sobre cada columna del DataFrame.
            if self.df[column].dtype == 'int64':    # Si la columna es de tipo int64, la convierte a int32.
                self.df[column] = self.df[column].astype('int32')
        
            if self.df[column].dtype == 'float64':  # Si la columna es de tipo float64, la convierte a float32.
                self.df[column] = self.df[column].astype('float32') 
                
                
    # Método para manejar las filas duplicadas en el DataFrame.
    def ManejoFilasDuplicadas(self):
        
        self.df.drop_duplicates(keep = 'first', inplace = True)  # Elimina las filas duplicadas, manteniendo la primera aparición.
    
    
    
    def GuardarDatos(self, ruta = './Datos Transformados', formato = 'csv'):
        
        if not os.path.exists(ruta):
            os.makedirs(ruta)
        
        archivo = f'{ruta}/{self.nombre}'
        if formato == 'csv':
            self.df.to_csv(f'{archivo}.csv', index = False)
        
        elif formato == 'excel':
            self.df.to_excel(f'{archivo}.xlsx', index = False)
        
        elif formato == 'parquet':
            self.df.to_parquet(f'{archivo}.parquet', index = False)
            
        else: 
            print('Formato no soportado. Por favor, utilice "csv", "excel" o "parquet".')
           
           
           
    def CargarDatos_MySQL(self, host, user, password, database):
        dtype_mapeo = {
            'int64': 'BIGINT',
            'int32': 'INT',
            'float64': 'FLOAT',
            'float32': 'FLOAT',
            'object': 'TEXT',  # Cambiar a TEXT para evitar problemas con datos largos
            'datetime64[ns]': 'DATETIME',
            'bool': 'BOOLEAN'
        }

        # Crear definición de columnas
        columns = ", ".join([
            f'`{col}` {dtype_mapeo.get(str(dtype), "TEXT")}'  # Usar TEXT como valor por defecto
            for col, dtype in self.df.dtypes.items()
            if col.lower() != 'id'  # Excluir la columna 'id' si existe
        ])
        
        # Definir el tamaño de VARCHAR para columnas que se espera que tengan texto largo
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{self.nombre}` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            {columns},
            INDEX (`id`)  # Añadir índice para la columna 'id'
        )
        """

        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            cursor = conn.cursor()

            # Crear tabla
            cursor.execute(create_table_query)

            # Insertar datos
            placeholders = ", ".join(["%s"] * len(self.df.columns))
            insert_query = f"""
            INSERT INTO `{self.nombre}` ({", ".join([f'`{col}`' for col in self.df.columns])})
            VALUES ({placeholders})
            """
            for _, row in self.df.iterrows():
                cursor.execute(insert_query, tuple(row))

            conn.commit()

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Algo falló con tu nombre de usuario o contraseña")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("La base de datos no existe")
            elif err.errno == errorcode.ER_DATA_TOO_LONG:
                print("Los datos son demasiado largos para una columna")
            elif err.errno == errorcode.ER_DUP_FIELDNAME:
                print("Nombre de columna duplicado en la definición de la tabla")
            else:
                print(err)
        finally:
            cursor.close()
            conn.close()
    
    
    
    
# Se crean instancias de la clase ETLProcessor para varios DataFrames, con sus respectivos nombres.
Transformacion_CalidadAire = ETLProcessor(Calidad_Aire, 'Calidad_Aire')
Transformacion_AlternativeFuel = ETLProcessor(Alternative_Fuel_Vehicles, 'Alternative_Fuel_Vehicles')
Transformacion_ElectricCarNorm = ETLProcessor(ElectricCarData_Norm, 'ElectricCarData_Norm')
Transformacion_ElectricCarClean = ETLProcessor(ElectricCarData_Clean, 'ElectricCarData_Clean')
Transformacion_LightDuty = ETLProcessor(Light_Duty_Vehicles, 'Light_Duty_Vehicles')
Transformacion_VehicleFuelEconomy = ETLProcessor(Vehicle_Fuel_Economy, 'Vehicle_Fuel_Economy')
Transformacion_TaxiZoneLookup = ETLProcessor(Taxi_zone_lookup, 'Taxi_Zone_Lookup')


# Se aplican las correspondientes instancias para cada DataFrame
for transformacion in [Transformacion_CalidadAire, Transformacion_AlternativeFuel, Transformacion_ElectricCarNorm, Transformacion_ElectricCarClean, 
                       Transformacion_LightDuty, Transformacion_VehicleFuelEconomy, Transformacion_TaxiZoneLookup]:
    transformacion.ManejoValoresNulos()
    transformacion.ManejoTiposDatos()
    transformacion.ManejoFilasDuplicadas()
    
# Se aplica la instancia para guardar los datos 
#for transformacion in [Transformacion_CalidadAire, Transformacion_AlternativeFuel, Transformacion_ElectricCarNorm, Transformacion_ElectricCarClean, 
 #                      Transformacion_LightDuty, Transformacion_VehicleFuelEconomy, Transformacion_TaxiZoneLookup]:
  #  transformacion.GuardarDatos()



# Se aplica la instancia para cargar los datos a una base de datos de MySQL
# for transformacion in [Transformacion_CalidadAire, Transformacion_AlternativeFuel, Transformacion_ElectricCarNorm, Transformacion_ElectricCarClean, 
#                        Transformacion_LightDuty, Transformacion_VehicleFuelEconomy, Transformacion_TaxiZoneLookup]:
#     transformacion.CargarDatos_MySQL(
#     host='localhost',
#     user='ProyectoFinalMySQL',
#     password='ProyectoFinal',
#     database='Proyecto_Final'
# )
Transformacion_VehicleFuelEconomy.CargarDatos_MySQL(
     host='localhost',
     user='ProyectoFinalMySQL',
     password='ProyectoFinal',
     database='Proyecto_Final')