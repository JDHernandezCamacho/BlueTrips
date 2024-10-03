import streamlit as st
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

# Cargar el modelo entrenado
@st.cache
def load_model():
    with open('random_forest_model.pkl', 'rb') as file:
        model = pickle.load(file)
    return model

model = load_model()

# Título de la aplicación
st.title('Predicción de Viajes Compartidos')

# Descripción breve
st.write("""
Esta aplicación predice si un viaje en taxi será compartido basado en varias características del viaje.
""")

# Entrada del usuario
st.header('Introduzca los detalles del viaje:')

passenger_count = st.selectbox('Cantidad de pasajeros', [2, 3])
trip_distance = st.number_input('Distancia del viaje (en millas)', min_value=0.0)
pickup_location = st.number_input('ID de la ubicación de recogida', min_value=0, step=1)
dropoff_location = st.number_input('ID de la ubicación de destino', min_value=0, step=1)
fare_amount = st.number_input('Monto de la tarifa', min_value=0.0)
total_amount = st.number_input('Monto total', min_value=0.0)

# Convertir las entradas en un DataFrame
input_data = pd.DataFrame({
    'passenger_count': [passenger_count],
    'trip_distance': [trip_distance],
    'PULocationID': [pickup_location],
    'DOLocationID': [dropoff_location],
    'fare_amount': [fare_amount],
    'total_amount': [total_amount]
})

# Botón para hacer la predicción
if st.button('Predecir si el viaje será compartido'):
    prediction = model.predict(input_data)
    result = 'compartido' if prediction[0] == 1 else 'no compartido'
    st.write(f'El viaje será {result}.')




