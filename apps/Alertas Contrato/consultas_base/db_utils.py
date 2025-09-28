"""
    Manejo de la base de datos (MySQL) para la app. 
"""
# Importaciones 
import pymysql
import pandas as pd
from configuraciones.confi import get_database_config

# Configuración conexión base de datos
DB_CONFIG = get_database_config()

class DatabaseUtils:
    """Clase para manejar las operaciones de la base de datos"""
    
    def conectar_bd(self):
        """Manejo de la conexión a la base de datos"""
        return pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset="utf8mb4"
        )

    def obtener_alertas(self):
        """Obtiene los datos de alertas desde la base de datos bases/contract_alerts"""
        sql = """
        SELECT 
            employee_name, employee_rut, employee_role,
            boss_name, boss_email,
            alert_date, alert_reason, expiration,
            days_since_start, employee_start_date,
            alert_type
        FROM contract_alerts 
        WHERE 
            NOT (alert_type = 'INDEFINIDO' AND second_alert_sent != 0)
        AND 
            NOT (alert_type = 'SEGUNDO_PLAZO' AND first_alert_sent != 0)
        ORDER BY alert_date ASC
        """
        try:
            with self.conectar_bd() as conexion:
                with conexion.cursor() as cursor:
                    cursor.execute(sql)
                    filas_alertas = cursor.fetchall()
            columnas = ["Empleado", "RUT", "Cargo", "Jefe", "Email Jefe",
                    "Fecha alerta", "Motivo", "Vencimiento", "Días desde inicio", "Fecha Vencimiento",
                    "Tipo Alerta"]
            return pd.DataFrame(filas_alertas, columns=columnas)
        except Exception as e:
            print(f"Error obteniendo alertas: {e}")
            return pd.DataFrame()
    
    # def obtener_incidencias(self):
    #     """Obtiene incidencias desde la base"""
    #     sql = """
    #         SELECT
    #             rut_empleado,
    #             fecha_inicio,
    #             fecha_fin,
    #             tipo_permiso
    #         FROM consolidado_incidencias
    #     """
    #     try:
    #         with self.conectar_bd() as conexion:
    #             with conexion.cursor() as cursor:
    #                 cursor.execute(sql)
    #                 rows = cursor.fetchall()
    #         cols = ["rut_empleado", "fecha_inicio", "fecha_fin", "tipo_permiso"]
    #         return pd.DataFrame(rows, columns=cols)
    #     except Exception as e:
    #         print(f"Error obteniendo incidencias: {e}")
    #         return pd.DataFrame()
        
    def obtener_tipo_alerta(self, employee_rut):
        """
        Obtiene el tipo de alerta para un empleado
        Returns:
            str: 'SEGUNDO_PLAZO' o 'INDEFINIDO' o None
        """
        conexion = None
        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            sql = """SELECT alert_type 
            FROM contract_alerts 
            WHERE employee_rut = %s"""
            cursor.execute(sql, (employee_rut,))
            
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
            
        except Exception as e:
            print(f"Error obteniendo tipo de alerta: {e}")
            return None
        finally:
            if conexion:
                cursor.close()
                conexion.close()

    #ya no es necesaria, pero sirve de doble verificación
    def verificar_alerta_procesada(self, employee_rut, alert_type):
        """
        Verifica si una alerta ya esta procesada
        Returns:
            bool: True si ya fue procesada, False si no
        """
        conexion = None
        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            #campos a verificar
            if alert_type == 'SEGUNDO_PLAZO':
                campo = 'first_alert_sent'
            elif alert_type == 'INDEFINIDO':
                campo = 'second_alert_sent'
            else:
                print(f"Tipo de alerta desconocido: {alert_type}")
                return False
            
            sql = f"""
                SELECT {campo} 
                FROM contract_alerts 
                WHERE employee_rut = %s
            """
            
            cursor.execute(sql, (employee_rut,))
            resultado = cursor.fetchone()
            
            if resultado:
                ya_procesada = bool(resultado[0])
                if ya_procesada:
                    print(f"Alerta ya procesada para {employee_rut} - omitiedo")
                return ya_procesada
            else:
                print(f"No se encontró registro parael rut: {employee_rut}")
                return False
                
        except Exception as e:
            print(f"Error verificando alerta procesada: {e}")
            return False
        finally:
            if conexion:
                cursor.close()
                conexion.close()

    def marcar_procesada(self, employee_rut, alert_type):
        """
        Marca una alerta como procesada/enviada en la base de datos
        """
        conexion = None
        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            if alert_type == 'SEGUNDO_PLAZO':
                campo = 'first_alert_sent = 1'
            elif alert_type == 'INDEFINIDO': 
                campo = 'second_alert_sent = 1, first_alert_sent = 1'
            else:
                print(f"Tipo de alerta desconocido: {alert_type}")
                return False
            
            sql = f"""
                UPDATE contract_alerts 
                SET {campo}, updated_at = NOW()
                WHERE employee_rut = %s
            """
            
            cursor.execute(sql, (employee_rut,))
            
            if cursor.rowcount > 0:
                conexion.commit()
                print(f"Alerta marcada como enviada - RUT: {employee_rut}")
                return True
            else:
                print(f"No se encontró registro para RUT: {employee_rut}")
                return False
                
        except Exception as e:
            if conexion:
                conexion.rollback()
            print(f"Error actualizando BD: {e}")
            return False
        finally:
            if conexion:
                cursor.close()
                conexion.close()

    