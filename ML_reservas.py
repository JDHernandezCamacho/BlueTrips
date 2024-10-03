import streamlit as st
import pandas as pd
import random
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

url = 'https://github.com/UrbanGreenSolutions/BlueTrips/blob/main/Datasets/complete_with_cars.csv'

# Cargar los datos
@st.cache_data
def load_data():
    return pd.read_csv(url)

complete = load_data()

# Pasar las columnas a formato datetime
complete['tpep_pickup_datetime'] = pd.to_datetime(complete['tpep_pickup_datetime'])
complete['tpep_dropoff_datetime'] = pd.to_datetime(complete['tpep_dropoff_datetime'])

# Calcular la duración del viaje en minutos
complete['trip_duration'] = (complete['tpep_dropoff_datetime'] - complete['tpep_pickup_datetime']).dt.total_seconds() / 60

# Convertir la columna 'placa' en variables dummy
X = pd.get_dummies(complete[['passenger_count', 'DOLocationID', 'placa']], drop_first=True)
y_costo = complete['total_amount']  # Costo del viaje
y_tiempo = complete['trip_duration']  # Tiempo de viaje en minutos

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train_costo, y_test_costo = train_test_split(X, y_costo, test_size=0.2, random_state=42)
X_train_tiempo, X_test_tiempo, y_train_tiempo, y_test_tiempo = train_test_split(X, y_tiempo, test_size=0.2, random_state=42)

# Entrenar los modelos
modelo_costo = DecisionTreeRegressor().fit(X_train, y_train_costo)
modelo_tiempo = DecisionTreeRegressor().fit(X_train_tiempo, y_train_tiempo)

# Crear el DataFrame de reservas
reservas = pd.DataFrame(columns=['nombre_cliente', 'apellido_cliente', 'fecha_servicio', 'hora_servicio', 
                                 'aeropuerto_llegada', 'zona_destino', 'num_pasajeros', 'placa', 'confirmacion'])

# Cargar reservas desde un archivo CSV si existe
try:
    reservas = pd.read_csv('reservas.csv')
except FileNotFoundError:
    pass  # Si no existe el archivo, continuar con el DataFrame vacío

# Función para generar un número de confirmación único
def generar_confirmacion():
    while True:
        confirmacion = random.randint(0, 1000)
        if confirmacion not in reservas['confirmacion'].values:
            return confirmacion

# Interfaz de usuario
st.title("Reserva de vehiculos compartidos")

nombre_cliente = st.text_input("Ingrese su nombre:")
apellido_cliente = st.text_input("Ingrese su apellido:")
fecha_servicio = st.date_input("Ingrese la fecha del servicio:")
hora_servicio = st.time_input("Ingrese la hora del servicio:")

# Crear una lista desplegable para seleccionar el aeropuerto
aeropuerto_opciones = {
    'Newark': 1,
    'La Guardia': 138,
    'JFK': 132
}
aeropuerto_llegada = st.selectbox("Seleccione el aeropuerto de llegada:", list(aeropuerto_opciones.keys()))

zona_destino = st.selectbox("Ingrese la zona o localidad de destino:", complete['Zone'].unique())

num_pasajeros = st.number_input("Ingrese la cantidad de pasajeros (máx 5):", min_value=1, max_value=5)

# Asegurarse de que no haya valores NaN en la columna 'Zone'
taxi_zones_clean = complete.dropna(subset=['Zone'])

if st.button("Reservar"):
    # Obtener el PULocationID basado en el aeropuerto seleccionado
    PULocationID = aeropuerto_opciones[aeropuerto_llegada]

    # Buscar DOLocationID de la zona ingresada
    location_data = taxi_zones_clean[taxi_zones_clean['Zone'].str.contains(zona_destino, case=False)]
    if location_data.empty:
        st.error("Zona no encontrada. Por favor, ingrese una zona válida.")
    else:
        DOLocationID = location_data.iloc[0]['LocationID']

        # Filtrar los taxis disponibles para el viaje
        taxis_disponibles = complete[(complete['passenger_count'] >= num_pasajeros) & 
                                     (complete['DOLocationID'] == DOLocationID)]

        if taxis_disponibles.empty:
            st.warning("No hay taxis disponibles para esta zona y número de pasajeros. Buscando otro vehículo...")
            taxis_disponibles = complete[complete['DOLocationID'] == DOLocationID]
            taxis_disponibles = taxis_disponibles[taxis_disponibles['passenger_count'] + num_pasajeros <= 5]
            
            if taxis_disponibles.empty:
                st.error("No hay taxis disponibles para esta zona.")
            else:
                placa_disponible = random.choice(taxis_disponibles['placa'].unique())
        else:
            # Verificar que el taxi no exceda el límite de 5 pasajeros sumando los pasajeros existentes
            placa_disponible = None
            for placa in taxis_disponibles['placa'].unique():
                pasajeros_existentes = reservas[(reservas['placa'] == placa) & 
                                                (reservas['fecha_servicio'] == fecha_servicio) & 
                                                (reservas['hora_servicio'] == hora_servicio)]['num_pasajeros'].sum()
                if pasajeros_existentes + num_pasajeros <= 5:
                    placa_disponible = placa
                    break

            if placa_disponible is None:
                st.warning("Todos los taxis disponibles para esta zona están llenos. Buscando otro vehículo...")
                placa_disponible = random.choice(taxis_disponibles['placa'].unique())

        # Preparar los datos de entrada para la predicción
        nueva_fila = pd.DataFrame({
            'passenger_count': [num_pasajeros],
            'DOLocationID': [DOLocationID],
            'PULocationID': [PULocationID]
        })
        placa_dummies = pd.get_dummies([placa_disponible], prefix='placa', drop_first=True)
        nueva_fila = pd.concat([nueva_fila, placa_dummies], axis=1)

        for col in X.columns:
            if col not in nueva_fila.columns:
                nueva_fila[col] = 0

        nueva_fila = nueva_fila[X.columns]

        # Hacer las predicciones
        pred_cost = modelo_costo.predict(nueva_fila)
        pred_time = modelo_tiempo.predict(nueva_fila)

        # Generar el número de confirmación
        confirmacion = generar_confirmacion()

        # Generar el mensaje final
        costo_viaje = round(pred_cost[0], 2)
        tiempo_viaje = round(pred_time[0], 2)

        mensaje = (f"Hola {nombre_cliente} {apellido_cliente}, ¡Gracias por elegir blue trips! Tu reserva para el día {fecha_servicio} ha sido confirmada. "
                   f"El taxi con placas {placa_disponible} te podrá recoger a las {hora_servicio} horas. "
                   f"El costo estimado de tu viaje es de ${costo_viaje} USD, y el tiempo del trayecto es de "
                   f"alrededor de {tiempo_viaje} minutos. Tu número de confirmación es {confirmacion}. "
                   "En unos minutos, el conductor se pondrá en contacto contigo para confirmar los detalles del servicio. ")
        if num_pasajeros <= 4:
            mensaje += " Aún hay disponibilidad para más pasajeros si deseas compartir el taxi."

        # Agregar la reserva a la base de datos
        nueva_reserva = pd.DataFrame({
            'nombre_cliente': [nombre_cliente],
            'apellido_cliente': [apellido_cliente],
            'fecha_servicio': [fecha_servicio],
            'hora_servicio': [hora_servicio],
            'aeropuerto_llegada': [aeropuerto_llegada],
            'zona_destino': [zona_destino],
            'num_pasajeros': [num_pasajeros],
            'placa': [placa_disponible],
            'confirmacion': [confirmacion]
        })
        reservas = pd.concat([reservas, nueva_reserva], ignore_index=True)

        # Guardar reservas en un archivo CSV
        reservas.to_csv('reservas.csv', index=False)

        st.success(mensaje)






          

