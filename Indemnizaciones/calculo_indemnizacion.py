#%%
#importaciones necesarias
import pandas as pd
from sqlalchemy import create_engine
import pymysql


# Configuración BD - windows
db_connection_str = 'mysql+pymysql://compensaciones_rrhh:_Cramercomp2025_@192.168.245.33/rrhh_app'


# info_conexion = {
#     'host': '192.168.245.33',
#     'user': 'compensaciones_rrhh',
#     'password': '_Cramercomp2025_',
#     'database': 'rrhh_app',     
# }

# try:
#     connection = pymysql.connect(**info_conexion)
#     print("Conexión a la base de datos exitosa!")
#     connection.close()
# except pymysql.MySQLError as e:
#     print(f"Error de conexión: {e}")


#%%
def obtener_datos():
    """Obtiene datos con info de jefatura, cargo y sueldo desde employees_jobs"""
    # try:
    #     conexion = pymysql.connect(**info_conexion)
    #     print("Conexión a la base de datos exitosa!")
    # except pymysql.MySQLError as e:
    #     print(f"Error de conexión: {e}")
    #     conexion = None
    #     return pd.DataFrame()
    try:
        engine = create_engine(db_connection_str)

        query = """
        SELECT
            e.person_id,
            e.rut,
            e.full_name AS Nombre,
            COALESCE(e.gender, 'N/A') AS Género,
            e.area_id AS ID_Area,
            COALESCE(e.contract_type, 'N/A') AS Tipo_Contrato,
            e.active_since,

            -- Historial desde employees_jobs
            ej.start_date,
            ej.end_date,
            ej.role_name AS Cargo_Actual,
            ej.base_wage AS Sueldo_Base,

            -- Área
            COALESCE(a.name, CONCAT('Área ', e.area_id)) AS Nombre_Area,

            -- Jefatura
            jefe.full_name AS Nombre_Jefe

        FROM employees_jobs ej
        JOIN employees e
            ON ej.person_rut = e.rut
        LEFT JOIN areas a
            ON e.area_id = a.id
        LEFT JOIN employees jefe
            ON ej.boss_rut = jefe.rut

        WHERE e.status = 'activo' AND ej.start_date >= '2018-01-01'
        ORDER BY e.full_name, ej.start_date;

        """
        df = pd.read_sql(query, engine)
        #df = pd.read_sql(query, conexion)

        if not df.empty:
            # Crear las columnas de fecha
            df['active_since'] = pd.to_datetime(df['active_since'], errors='coerce')
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')

            # Calcular Años_de_Servicio usando active_since (es la antigüedad del empleado)
            df["Años_de_Servicio"] = (pd.to_datetime("today").year - df["active_since"].dt.year).fillna(0)

            df['Período'] = df['start_date'].dt.to_period('M').astype(str)
            df['Año'] = df['start_date'].dt.year
            df['Mes'] = df['start_date'].dt.month

            df['sueldo_base'] = df['Sueldo_Base']
            
        return df
    
    except Exception as e:
        print(f"Error SQL: Error consultando datos:\n{e}")
        return pd.DataFrame()

    finally:
        # Asegúrate de cerrar la conexión de manera segura
        if 'engine' in locals():
            engine.dispose()
    # finally:
    #     if 'conexion' in locals() and conexion:
    #         conexion.close()
    
#%%
df_datos = obtener_datos()
if not df_datos.empty:
    print("DataFrame creado. Columnas:")
    print(df_datos.columns)
else:
    print("No se pudo obtener el DataFrame.")
# %%
