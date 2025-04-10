
import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="🎰 App Casino: Seguimiento de Jugadores", layout="wide")

st.title("📊 Análisis de Jugadores del Casino")

seccion = st.sidebar.radio("Seleccioná una sección:", ["🔝 Top 10 de Cargas", "📉 Reactivación por Segmento", "🗓️ Filtro de Jugadores Inactivos"])

# --- FUNCIONES AUXILIARES ---
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

# --- SECCIÓN TOP 10 ---
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
            st.subheader("💰 Top por Monto")
            st.dataframe(top_monto)
            st.subheader("🔢 Top por Cantidad")
            st.dataframe(top_cant)

# --- SECCIÓN DE REACTIVACIÓN POR SEGMENTO ---
elif seccion == "📉 Reactivación por Segmento":
    st.header("📉 Reactivación Inteligente por Segmento")
    archivo = st.file_uploader("📁 Subí archivo de cargas (inactivos):", type=["xlsx", "xls", "csv"], key="inactivos_seg")

    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)
        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            df = df[df["Tipo"] == "in"]
            hoy = pd.to_datetime(datetime.date.today())
            ultima = df.groupby("Jugador")["Fecha"].max().reset_index()
            ultima["Dias_inactivo"] = (hoy - ultima["Fecha"]).dt.days

            def mensaje(jugador, dias):
                if 6 <= dias <= 13:
                    return ("Inactivo reciente", f"Hola {jugador}, hace {dias} días que no te vemos. ¡Volvé con un bono del 50%! 🎁")
                elif 14 <= dias <= 22:
                    return ("Semi-perdido", f"{jugador}, volvé y duplicamos tu saldo. Hace {dias} días que no jugás. 🔥")
                elif 23 <= dias <= 30:
                    return ("Inactivo prolongado", f"{jugador}, hace {dias} días que no cargás. Te espera una oferta exclusiva. 💬")
                return ("", "")

            ultima[["Segmento", "Mensaje"]] = ultima.apply(lambda row: pd.Series(mensaje(row["Jugador"], row["Dias_inactivo"])), axis=1)
            df_resultado = ultima[ultima["Segmento"] != ""].sort_values(by="Dias_inactivo", ascending=False)

            st.subheader("🎯 Jugadores Segmentados con Mensaje")
            enviados = []
            for _, row in df_resultado.iterrows():
                with st.expander(f"{row['Jugador']} ({row['Dias_inactivo']} días inactivo)"):
                    st.markdown(f"**Segmento:** {row['Segmento']}")
                    st.text_area("📨 Mensaje personalizado", value=row["Mensaje"], key=row["Jugador"])
                    enviado = st.checkbox("✅ Mensaje enviado", key=f"enviado_{row['Jugador']}")
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

# --- SECCIÓN DE FILTRO SIMPLE POR DÍAS ---
elif seccion == "🗓️ Filtro de Jugadores Inactivos":
    st.header("🗓️ Filtro de Jugadores por Inactividad")
    archivo = st.file_uploader("📁 Subí archivo con historial de cargas:", type=["xlsx", "xls", "csv"], key="filtro_dias")
    min_dias = st.number_input("📅 Mostrar jugadores que no cargan hace al menos X días:", min_value=1, max_value=60, value=6)

    if archivo:
        df = pd.read_excel(archivo) if archivo.name.endswith((".xlsx", ".xls")) else pd.read_csv(archivo)
        df = preparar_dataframe(df)
        if df is not None:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
            df = df[df["Tipo"] == "in"]
            hoy = pd.to_datetime(datetime.date.today())
            ultima = df.groupby("Jugador")["Fecha"].max().reset_index()
            ultima["Dias_inactivo"] = (hoy - ultima["Fecha"]).dt.days
            filtrado = ultima[ultima["Dias_inactivo"] >= min_dias].sort_values(by="Dias_inactivo", ascending=False)

            st.subheader(f"👥 Jugadores que no cargan hace al menos {min_dias} días")
            st.dataframe(filtrado)

            filtrado.to_excel("jugadores_filtrados_por_dias.xlsx", index=False)
            with open("jugadores_filtrados_por_dias.xlsx", "rb") as f:
                st.download_button("📥 Descargar Excel", f, file_name="jugadores_filtrados_por_dias.xlsx")
