
import streamlit as st
import pandas as pd
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="App de Cargas - Casino", layout="wide")

st.title("🎰 App de Análisis de Cargas del Casino")

seccion = st.sidebar.radio("Seleccioná una sección:", [
    "🔝 Top 10 de Cargas",
    "📉 Jugadores Inactivos",
    "🗓️ Filtro desde Google Sheet"
])

# Conexión a Google Sheet
def obtener_df_desde_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive.readonly"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1kx4yZw-mvD0xlbOIGNMj2vb_WUM0uW5X6yWeoI3e0fw").worksheet("Fénix")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Formato base
def preparar_dataframe(df):
    df = df.rename(columns={
        "operación": "Tipo",
        "Depositar": "Monto",
        "Retirar": "?1",
        "Wager": "?2",
        "Límites": "?3",
        "Balance antes de operación": "Saldo",
        "Fecha": "Fecha",
        "Tiempo": "Hora",
        "Iniciador": "UsuarioSistema",
        "Del usuario": "Plataforma",
        "Sistema": "Admin",
        "Al usuario": "Jugador",
        "IP": "Extra"
    })
    columnas_esperadas = [
        "ID", "Tipo", "Monto", "?1", "?2", "?3", "Saldo",
        "Fecha", "Hora", "UsuarioSistema", "Plataforma", "Admin", "Jugador", "Extra"
    ]
    if len(df.columns) == len(columnas_esperadas):
        df.columns = columnas_esperadas
        return df
    else:
        return None

# 🔝 Sección TOP 10
if seccion == "🔝 Top 10 de Cargas":
    st.header("🔝 Top 10 por Monto y Cantidad de Cargas")
    archivo = st.file_uploader("📁 Subí tu archivo de cargas recientes:", type=["xlsx", "xls", "csv"], key="top10")
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)
        if df is not None:
            df = df[df["Tipo"] == "in"]
            df["Fecha"] = pd.to_datetime(df["Fecha"])

            top_monto = df.groupby("Jugador").agg(Monto_Total_Cargado=("Monto", "sum"), Cantidad_Cargas=("Jugador", "count")).sort_values(by="Monto_Total_Cargado", ascending=False).head(10).reset_index()
            top_cant = df.groupby("Jugador").agg(Cantidad_Cargas=("Jugador", "count"), Monto_Total_Cargado=("Monto", "sum")).sort_values(by="Cantidad_Cargas", ascending=False).head(10).reset_index()

            st.subheader("💰 Top 10 por Monto Total Cargado")
            st.dataframe(top_monto)
            st.subheader("🔢 Top 10 por Cantidad de Cargas")
            st.dataframe(top_cant)

            writer = pd.ExcelWriter("Top10_Cargas.xlsx", engine="xlsxwriter")
            top_monto.to_excel(writer, sheet_name="Top Monto", index=False)
            top_cant.to_excel(writer, sheet_name="Top Cantidad", index=False)
            writer.close()

            with open("Top10_Cargas.xlsx", "rb") as f:
                st.download_button("📥 Descargar Excel", f, file_name="Top10_Cargas.xlsx")
        else:
            st.error("❌ El archivo no tiene el formato esperado.")

# 📉 Sección Jugadores Inactivos con mensajes
elif seccion == "📉 Jugadores Inactivos":
    st.header("📉 Detección y Segmentación de Jugadores Inactivos")
    archivo = st.file_uploader("📁 Subí tu archivo con historial amplio de cargas:", type=["xlsx", "xls", "csv"], key="inactivos")
    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)
        if df is not None:
            df = df[df["Tipo"] == "in"]
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            hoy = pd.to_datetime(datetime.date.today())
            ultima_carga = df.groupby("Jugador")["Fecha"].max().reset_index()
            ultima_carga["Dias_inactivo"] = (hoy - ultima_carga["Fecha"]).dt.days

            def mensaje(jugador, dias):
                if 6 <= dias <= 13:
                    return ("Inactivo reciente", f"Hola {jugador}, hace {dias} días que no te vemos. ¡Volvé con un bono del 50%! 🎁")
                elif 14 <= dias <= 22:
                    return ("Semi-perdido", f"{jugador}, volvé y duplicamos tu saldo. Hace {dias} días que no jugás. 🔥")
                elif 23 <= dias <= 30:
                    return ("Inactivo prolongado", f"{jugador}, hace {dias} días que no cargás. Te espera una oferta exclusiva. 💬")
                return ("", "")

            ultima_carga[["Segmento", "Mensaje"]] = ultima_carga.apply(lambda row: pd.Series(mensaje(row["Jugador"], row["Dias_inactivo"])), axis=1)
            resultado = ultima_carga[ultima_carga["Segmento"] != ""].sort_values(by="Dias_inactivo", ascending=False)

            st.subheader("🎯 Jugadores Segmentados con Mensaje")
            enviados = []
            for _, row in resultado.iterrows():
                with st.expander(f"{row['Jugador']} ({row['Dias_inactivo']} días inactivo)"):
                    st.markdown(f"**Segmento:** {row['Segmento']}")
                    st.text_area("📨 Mensaje personalizado", value=row["Mensaje"], key=row["Jugador"])
                    enviado = st.checkbox("✅ Mensaje enviado", key=f"check_{row['Jugador']}")
                    enviados.append({
                        "Jugador": row["Jugador"],
                        "Días inactivo": row["Dias_inactivo"],
                        "Segmento": row["Segmento"],
                        "Mensaje": row["Mensaje"],
                        "Mensaje enviado": enviado
                    })

            df_enviados = pd.DataFrame(enviados)
            df_enviados.to_excel("seguimiento_segmentado.xlsx", index=False)
            with open("seguimiento_segmentado.xlsx", "rb") as f:
                st.download_button("📥 Descargar seguimiento", f, file_name="seguimiento_segmentado.xlsx")

# 🗓️ Filtro desde Google Sheet
elif seccion == "🗓️ Filtro desde Google Sheet":
    st.header("🗓️ Filtro de Jugadores por Inactividad (Google Sheet)")
    df = obtener_df_desde_sheet()
    hoy = pd.to_datetime(datetime.date.today())
    df["Última vez que cargó"] = pd.to_datetime(df["Última vez que cargó"], errors="coerce")
    df["Dias_inactivo"] = (hoy - df["Última vez que cargó"]).dt.days

    min_dias = st.number_input("📅 Mostrar jugadores que no cargan hace al menos X días:", min_value=1, max_value=90, value=6)
    filtrados = df[df["Dias_inactivo"] >= min_dias].sort_values(by="Dias_inactivo", ascending=False)

    st.subheader(f"👥 Jugadores con más de {min_dias} días sin cargar")
    st.dataframe(filtrados)

    filtrados.to_excel("jugadores_inactivos_desde_sheet.xlsx", index=False)
    with open("jugadores_inactivos_desde_sheet.xlsx", "rb") as f:
        st.download_button("📥 Descargar Excel", f, file_name="jugadores_inactivos_desde_sheet.xlsx")
