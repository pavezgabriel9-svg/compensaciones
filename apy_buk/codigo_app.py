import streamlit as st
import pandas as pd
import pymysql
import win32com.client as win32  # <-- usamos Outlook



import pythoncom

def enviar_email_outlook(df):
    try:
        pythoncom.CoInitialize()   # <-- la magia 🔮
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.To = MAIL_TEST
        mail.Subject = f"🚨 Reporte de alertas de contratos ({len(df)} pendientes)"

        # Construir tabla HTML
        html = "<h3>Reporte de Alertas</h3><table border='1' cellpadding='4'>"
        html += "<tr>" + "".join([f"<th>{c}</th>" for c in df.columns]) + "</tr>"
        for _, row in df.iterrows():
            html += "<tr>" + "".join([f"<td>{row[c]}</td>" for c in df.columns]) + "</tr>"
        html += "</table>"

        mail.HTMLBody = html
        mail.Send()

        pythoncom.CoUninitialize()
        return True

    except Exception as e:
        st.error(f"❌ Error al enviar correo con Outlook: {e}")
        return False

# ========== CONFIG BD ==========
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# ========== CONFIG EMAIL ==========
MAIL_TEST = "gpavez@cramer.cl"   # tu correo de pruebas

# ========== FUNCIONES ==========

def conectar_bd():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )

def obtener_alertas():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    sql = """
    SELECT 
        employee_name, employee_rut, employee_role,
        employee_area_name, boss_name, boss_email,
        alert_date, alert_reason,
        days_since_start,
        DATEDIFF(alert_date, CURDATE()) as dias_hasta_alerta,
        is_urgent, requires_action
    FROM contract_alerts 
    WHERE processed = FALSE
    ORDER BY alert_date ASC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    cols = ["Empleado","RUT","Cargo","Área","Jefe","Email Jefe",
            "Fecha alerta","Motivo","Días desde inicio",
            "Días hasta alerta","Urgente","Requiere Acción"]
    df = pd.DataFrame(rows, columns=cols)
    cursor.close()
    conexion.close()
    return df


def enviar_email_outlook(df):
    """
    Envía el reporte al correo de prueba usando Outlook
    """
    try:
        outlook = win32.Dispatch("outlook.application")
        mail = outlook.CreateItem(0)
        mail.To = MAIL_TEST
        mail.Subject = f"🚨 Reporte de alertas de contratos ({len(df)} pendientes)"

        # Construir tabla HTML
        html = "<h3>Reporte de Alertas</h3><table border='1' cellpadding='4'>"
        html += "<tr>" + "".join([f"<th>{c}</th>" for c in df.columns]) + "</tr>"
        for _, row in df.iterrows():
            html += "<tr>" + "".join([f"<td>{row[c]}</td>" for c in df.columns]) + "</tr>"
        html += "</table>"

        mail.HTMLBody = html
        mail.Send()

        return True
    except Exception as e:
        st.error(f"❌ Error al enviar correo con Outlook: {e}")
        return False


# ========== APP STREAMLIT ==========
st.title("📊 Dashboard de Alertas de Contratos")

df = obtener_alertas()

if df.empty:
    st.info("✅ No hay alertas activas en este momento.")
else:
    st.metric("Total alertas activas", len(df))
    st.metric("Urgentes (<=7 días)", (df["Urgente"] == 1).sum())
    st.metric("Requieren acción", (df["Requiere Acción"] == 1).sum())

    st.subheader("Detalles")
    st.dataframe(df)

    if st.button("📧 Enviar reporte de prueba (Outlook)"):
        if enviar_email_outlook(df):
            st.success(f"✅ Reporte enviado a {MAIL_TEST}")