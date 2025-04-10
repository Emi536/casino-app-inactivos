
import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="🧠 Filtro de Jugadores desde Google Sheet", layout="wide")

st.title("🗂️ Jugadores Inactivos - Conexión Automática a Google Sheets")

# Configurar acceso a Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive.readonly"]
creds = ServiceAccountCredentials.from_json_keyfile_name("app-casino-456422-820c2f207c4b.json", scope)
client = gspread.authorize(creds)

# Cargar hoja "Fénix" desde Google Sheets
SHEET_ID = "1kx4yZw-mvD0xlbOIGNMj2vb_WUM0uW5X6yWeoI3e0fw"
sheet = client.open_by_key(SHEET_ID).worksheet("Fénix")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Procesamiento de fechas
hoy = pd.to_datetime(datetime.date.today())
df["Última vez que cargó"] = pd.to_datetime(df["Última vez que cargó"], errors="coerce")
df["Dias_inactivo"] = (hoy - df["Última vez que cargó"]).dt.days

# Filtro dinámico
min_dias = st.number_input("📅 Mostrar jugadores que no cargan hace al menos X días:", min_value=1, max_value=90, value=6)
filtrados = df[df["Dias_inactivo"] >= min_dias].sort_values(by="Dias_inactivo", ascending=False)

# Mostrar resultados
st.subheader(f"👥 Jugadores con más de {min_dias} días sin cargar")
st.dataframe(filtrados)

# Descargar resultados
filtrados.to_excel("jugadores_inactivos_desde_sheet.xlsx", index=False)
with open("jugadores_inactivos_desde_sheet.xlsx", "rb") as f:
    st.download_button("📥 Descargar Excel con jugadores filtrados", f, file_name="jugadores_inactivos_desde_sheet.xlsx")
