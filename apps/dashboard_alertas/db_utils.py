#-----------------------------------------------------------
#                    Conexión BD
#-----------------------------------------------------------
import pymysql
from tkinter import messagebox
import pandas as pd
from config import get_database_config

DB_CONFIG = get_database_config()
DB_HOST = DB_CONFIG['host']
DB_USER = DB_CONFIG['user']
DB_PASSWORD = DB_CONFIG['password']
DB_NAME = DB_CONFIG['database']

def conectar_bd():
        """Conecta a la base de datos"""
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4"
            )
        except Exception as e:
            messagebox.showerror("Error BD", f"Error conectando a la base de datos:\n{e}")
            return None

def obtener_alertas():
        """Obtiene los datos desde la base de datos"""
        conexion = conectar_bd()
        if not conexion:
            return pd.DataFrame()
        
        try:
            cursor = conexion.cursor()
            sql = """
            SELECT 
                id, employee_name, employee_rut, employee_role,
                employee_area_name, boss_name, boss_email,
                alert_date, alert_reason,
                days_since_start, employee_start_date,
                CAST(DATEDIFF(alert_date, CURDATE()) AS SIGNED) as dias_hasta_alerta,
                is_urgent, requires_action, alert_type
            FROM contract_alerts 
            WHERE processed = FALSE
            ORDER BY alert_date ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            cols = ["ID", "Empleado", "RUT", "Cargo", "Área", "Jefe", "Email Jefe",
                    "Fecha alerta", "Motivo", "Días desde inicio", "Fecha inicio",
                    "Días hasta alerta", "Urgente", "Requiere Acción", "Tipo Alerta"]
            
            df = pd.DataFrame(rows, columns=cols)
            cursor.close()
            conexion.close()
            return df
            
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo alertas:\n{e}")
            conexion.close()
            return pd.DataFrame()
    
    
def obtener_incidencias():
    """Obtiene los datos de incidencias desde la base de datos."""
    conexion = conectar_bd()
    if not conexion:
        print("sin conexion")
        return pd.DataFrame()
    else:
        print("Conexión exitosa")

    try:
        cursor = conexion.cursor()
        sql = """
        SELECT
            rut_empleado AS employee_rut ,
            fecha_inicio,
            fecha_fin,
            tipo_permiso
        FROM consolidado_incidencias
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        cols = ["rut_empleado", "fecha_inicio", "fecha_fin", "tipo_permiso"]
        incidencias_df = pd.DataFrame(rows, columns=cols)
        cursor.close()
        conexion.close()
        return incidencias_df
        
    except Exception as e:
        messagebox.showerror("Error", f"Error obteniendo incidencias:\n{e}")
        conexion.close()
        return pd.DataFrame()
    
