import streamlit as st

# Título e introducción
st.title("Dashboard de Power BI")
st.markdown("***")

# Reemplaza 'URL_DEL_DASHBOARD' con el enlace de tu dashboard de Power BI
power_bi_url = '<iframe title="Dashborad BlueTrips" width="1140" height="541.25" src="https://app.powerbi.com/view?r=eyJrIjoiOWZiNmE5YTgtZTdmYi00MDFmLTgzM2EtOTMwZjM0MTk1OWRmIiwidCI6ImUzY2FmODdlLWY3NmYtNGY3NS04ZWY5LWI1YTE2ZDIyNzQwMCIsImMiOjR9" frameborder="0" allowFullScreen="true"></iframe>'

# Usa el componente write para insertar el iframe
st.write(power_bi_url, unsafe_allow_html=True)