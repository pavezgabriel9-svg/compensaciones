import pandas as pd
from confi.confi_conn_db import configuracion_conexion

def obtener_datos():
    """
    OBTIENE LOS DATOS DEL HISTORIAL LABORAL DE LOS EMPLEADOS (DATAFRAME PRINCIPAL).
    """
    engine = configuracion_conexion()
    if not engine:
        print("Error de conexión a la base de datos.")
        return pd.DataFrame()
    try:
        with open("apps/app_com/APP Compensaciones/querys/obtener_datos_query.sql", "r", 
                  encoding="utf-8") as f:
            query = f.read()

        df = pd.read_sql(query, engine)
        if not df.empty:
            df['active_since'] = pd.to_datetime(df['active_since'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            df["service_years"] = (pd.to_datetime("today").year - df["active_since"].dt.year).fillna(0)
            df['period'] = df['start_date'].dt.to_period('M').astype(str)
            df['years'] = df['start_date'].dt.year
            df['month'] = df['start_date'].dt.month
         
        print("Datos de historial laboral obtenidos correctamente.")
        return df
    except Exception as e:
        print(f"Error al consultar historial laboral: {e}")
        return pd.DataFrame()

def obtener_datos_liquidaciones():
    """
    OBTIENE LOS DATOS HISTÓRICOS DE LIQUIDACIONES.
    """
    engine = configuracion_conexion()
    if not engine:
        print("Error de conexión a la base de datos.")
        return pd.DataFrame()
    try:
        # Asegúrate que la ruta sea correcta
        with open('apps/app_com/APP Compensaciones/querys/obtener_liquidaciones_query.sql', "r", 
                  encoding="utf-8") as f: 
            query = f.read()
        df = pd.read_sql(query, engine)

        if not df.empty:
            # Procesamiento de fechas (¡muy importante para el gráfico!)
            df['Pay_Period'] = pd.to_datetime(df['Pay_Period'], errors='coerce')
            df.dropna(subset=['Pay_Period', 'rut', 'Liquido_a_Pagar'], inplace=True)

        print("Datos de liquidaciones obtenidos correctamente.")
        return df
    except Exception as e:
        print(f"Error al consultar liquidaciones: {e}")
        return pd.DataFrame()

def obtener_datos_empleados():
    """
    OBTIENE LOS DATOS MAESTROS DE EMPLEADOS (INFO PERSONAL, CONTACTO, ETC.).
    """
    engine = configuracion_conexion()
    if not engine:
        print("Error de conexión a la base de datos.")
        return pd.DataFrame()
    try:
        with open('apps/app_com/APP Compensaciones/querys/obtener_empleados_query.sql', "r", 
                  encoding="utf-8") as f: 
            query = f.read()
        df = pd.read_sql(query, engine)
        print("Datos maestros de empleados obtenidos correctamente.")
        return df
    except Exception as e:
        print(f"Error al consultar datos de empleados: {e}")
        return pd.DataFrame()