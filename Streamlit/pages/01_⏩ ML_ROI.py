import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from google.cloud import bigquery
from google.oauth2 import service_account

# Configuración inicial de la aplicación
st.title("Análisis de ROI para vehículos eléctricos compartidos")

# Autenticación con BigQuery
credentials = service_account.Credentials.from_service_account_file(
    'C:\\Users\\Juan Pablo\\Desktop\\proyecto final Henry\\nomadic-mesh-436922-r3-e78534bb2f77.json'
)

# Crear cliente BigQuery
client = bigquery.Client(credentials=credentials, project='nomadic-mesh-436922-r3')

# Función para cargar datos desde BigQuery
@st.cache_data
def load_data_from_bigquery():
    query = """
    SELECT * FROM `nomadic-mesh-436922-r3.BlueTripsNY.Complete_With_Cars`
    """
    df = client.query(query).to_dataframe()
    return df

# Título de la app
st.title("Análisis de ROI para vehículos eléctricos compartidos")

complete_with_cars = load_data_from_bigquery() 

# Eliminar vehículos duplicados por 'Brand', 'Model' y 'Range_Km'
complete_with_cars = complete_with_cars.drop_duplicates(subset=['Brand', 'Model', 'Range_Km'])

# Convertir la distancia de millas a kilómetros
complete_with_cars['trip_distance_km'] = complete_with_cars['trip_distance'] * 1.60934

# Crear una columna para la eficiencia (consumo energético) en Wh/km
complete_with_cars['energy_consumed_kwh'] = (complete_with_cars['trip_distance_km'] * complete_with_cars['Efficiency_WhKm']) / 1000

# Asignar un costo promedio por kWh en USD
electricity_cost_per_kwh = 0.13 * euro_to_usd  # Convertir a dólares

# Calcular el costo mensual de carga eléctrica (suponiendo 2000 km recorridos al mes)
average_km_per_month = 2000
complete_with_cars['monthly_charge_cost'] = (average_km_per_month * complete_with_cars['Efficiency_WhKm'] / 1000) * electricity_cost_per_kwh

# Crear columnas de ingresos y costos mensuales en USD
complete_with_cars['monthly_revenue'] = 3000 * euro_to_usd  # Ingresos mensuales estimados (convertidos a dólares)
complete_with_cars['total_monthly_cost'] = complete_with_cars['monthly_charge_cost'] + 500 * euro_to_usd  # Costos operativos estimados (en dólares)

# Calcular la ganancia neta mensual
complete_with_cars['net_monthly_profit'] = complete_with_cars['monthly_revenue'] - complete_with_cars['total_monthly_cost']

# Limpiar los valores no numéricos
complete_with_cars.replace('-', np.nan, inplace=True)

# Verificar y eliminar valores faltantes en las columnas predictoras
complete_with_cars.dropna(subset=['Range_Km', 'PriceEuro', 'Efficiency_WhKm', 'Seats', 'TopSpeed_KmH', 'FastCharge_KmH', 'PowerTrain'], inplace=True)

# Convertir la columna 'PowerTrain' a variables dummy
complete_with_cars = pd.get_dummies(complete_with_cars, columns=['PowerTrain'], drop_first=True)

# Definir las variables predictoras (features) y la variable objetivo (target)
X = complete_with_cars[['Range_Km', 'PriceEuro', 'Efficiency_WhKm', 'Seats', 'TopSpeed_KmH', 'FastCharge_KmH'] + [col for col in complete_with_cars.columns if 'PowerTrain_' in col]]
y = complete_with_cars['net_monthly_profit']  # Nuestro target será la ganancia neta mensual

# Dividir el dataset en conjunto de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crear y entrenar el modelo de regresión lineal
linear_model = LinearRegression()
linear_model.fit(X_train, y_train)

# Crear y entrenar un modelo RandomForestRegressor como alternativa
rf_model = RandomForestRegressor(random_state=42)
rf_model.fit(X_train, y_train)

# Evaluar el modelo
linear_model_score = linear_model.score(X_test, y_test)
rf_model_score = rf_model.score(X_test, y_test)

# Solicitar el número de vehículos al usuario
num_vehicles = st.number_input("¿Cuántos vehículos desea invertir?", min_value=1, step=1, value=1)

# Seleccionar los vehículos con mayor autonomía
top_5_vehicles = complete_with_cars.nlargest(5, 'Range_Km')[['Brand', 'Model', 'Range_Km', 'PriceEuro', 'Efficiency_WhKm']]

# Convertir precios de euros a dólares para los vehículos
top_5_vehicles['PriceUSD'] = top_5_vehicles['PriceEuro'] * euro_to_usd

# Crear lista de opciones para la lista desplegable
vehicle_options = [f"{vehicle.Brand} {vehicle.Model} - Autonomía: {vehicle.Range_Km} km, Precio: ${vehicle.PriceUSD:.2f}" for vehicle in top_5_vehicles.itertuples()]

# Solicitar al usuario que seleccione un vehículo de la lista desplegable
selected_vehicle_option = st.selectbox("Seleccione el vehículo que desea:", vehicle_options)

# Obtener el índice del vehículo seleccionado
selected_vehicle_index = vehicle_options.index(selected_vehicle_option)
selected_vehicle = top_5_vehicles.iloc[selected_vehicle_index]

# Calcular el consumo mensual del vehículo seleccionado
energy_consumed_per_month = (average_km_per_month * selected_vehicle['Efficiency_WhKm']) / 1000  # Convertir Wh a kWh
monthly_charge_cost = energy_consumed_per_month * electricity_cost_per_kwh

# Cálculo de costos
maintenance_cost_per_year = 500 * euro_to_usd  # Convertido a dólares
tlc_license = 252 / 36  # Licencia TLC mensual (ya en USD)
insurance = 4500 / 12  # Seguro comercial mensual (ya en USD)
inspection = 180 / 12  # Inspección TLC mensual (ya en USD)
dmv_registration = 100 / 12  # Registro DMV mensual (ya en USD)

# Costo total mensual de operación
total_monthly_costs = (monthly_charge_cost + (maintenance_cost_per_year / 12) +
                       tlc_license + insurance + inspection + dmv_registration)

# Calcular la ganancia neta mensual con el modelo de ML
vehicle_features = np.array([[selected_vehicle['Range_Km'], selected_vehicle['PriceEuro'], selected_vehicle['Efficiency_WhKm'], 5] + [0]*(X_train.shape[1]-4)])  # Ajustamos las características
predicted_net_profit = linear_model.predict(vehicle_features)[0] * euro_to_usd  # Convertir el resultado a dólares

# Cálculo de la inversión inicial en la flota de vehículos
total_rebate = 1788.36 * num_vehicles * euro_to_usd
total_tax_credit = 6706.35 * num_vehicles * euro_to_usd
vehicle_costs = selected_vehicle['PriceUSD'] * num_vehicles - total_rebate - total_tax_credit

# Cálculo del ROI y Payback Period
net_monthly_profit_total = predicted_net_profit * num_vehicles
if net_monthly_profit_total > 0:
    payback_period_months = vehicle_costs / net_monthly_profit_total
else:
    payback_period_months = float('inf')  # Si la ganancia es negativa, no es posible recuperar la inversión

# Calcular el ROI
roi_percentage = (net_monthly_profit_total / vehicle_costs) * 100

# Mensaje final con la estructura solicitada
st.write(f"**Estimado usuario,**")
st.write(f"Has seleccionado {num_vehicles} unidades del modelo **{selected_vehicle['Brand']} {selected_vehicle['Model']}** con una autonomía de **{selected_vehicle['Range_Km']} km** y precio de **${selected_vehicle['PriceUSD']:.2f}**.")
st.write(f"Después de evaluar los costos iniciales y operativos de implementar una flota de vehículos eléctricos compartidos, hemos calculado el Retorno de Inversión (ROI) para tu inversión.")
st.write("**Resultados del análisis:**")
st.write(f"• Inversión inicial en la flota de vehículos eléctricos: **${vehicle_costs:.2f}**.")
st.write(f"• Costo operativo mensual por vehiculo (carga eléctrica y mantenimiento): **${total_monthly_costs:.2f}**.")
st.write(f"• Ingresos mensuales estimados por vehiculo: **${predicted_net_profit:.2f}**.")
st.write(f"• Ganancia neta mensual proyectada para la flota: **${net_monthly_profit_total:.2f}**.")

# Mensaje sobre el ROI y la recuperación de la inversión
if payback_period_months == float('inf'):
    st.write("No es posible recuperar la inversión con los ingresos y costos actuales.")
else:
    st.write(f"Con estos datos, hemos proyectado que recuperarás tu inversión en un plazo de **{payback_period_months:.0f} meses**.")
    st.write(f"A lo largo de este período, generarás un retorno del **{roi_percentage:.2f}%** sobre tu inversión inicial.")
    st.write("Esto indica que tu proyecto no solo es viable, sino que también será altamente rentable en un plazo razonable.")

