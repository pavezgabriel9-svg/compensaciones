#%% Librerías
import pymysql
import time
import datetime
from datetime import timedelta
import sys

#%% Configuración base de datos

# Configuración BD - windows
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# # Configuración BD - mac
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "conexion_buk"

#%% Función para calcular la fecha de alerta
def calcular_fecha_alerta(empleado):
    """
    Calcula la fecha de alerta según el tipo de contrato y status.
    """
    tipo_contrato = (empleado.get("contract_type") or "").lower()
    status = (empleado.get("status") or "").lower()
    metodo_pago = (empleado.get("payment_method") or "").lower()
    fecha_activacion = empleado.get("active_since")
    termino_primer_plazo = empleado.get("contract_finishing_date_1")
    termino_segundo_plazo = empleado.get("contract_finishing_date_2")
    
    # Solo considerar empleados activos con transferencia bancaria o tipo de contrato fijo
    if status != "activo" or metodo_pago != "transferencia bancaria" or tipo_contrato == "indefinido":
        return None
    
    try:
        if fecha_activacion:
            fecha_activacion = datetime.datetime.strptime(fecha_activacion, "%Y-%m-%d")
            primer_plazo = datetime.datetime.strptime(termino_primer_plazo, "%Y-%m-%d") if termino_primer_plazo else None
            segundo_plazo = datetime.datetime.strptime(termino_segundo_plazo, "%Y-%m-%d") if termino_segundo_plazo else None
        else:
            return None
        
        fecha_alerta, motivo, tipo_alerta = None, None, None
        
        # Primera alerta → paso a segundo plazo
        if tipo_contrato == "fijo" and primer_plazo is not None and segundo_plazo is not None:
            fecha_alerta = primer_plazo - timedelta(days=0) # Alerta el mismo día del término del primer plazo
            motivo = "Renovación a segundo plazo"
            tipo_alerta = "SEGUNDO_PLAZO"
            dias_vencimiento = (datetime.datetime.now() - fecha_alerta).days
        
        # Segunda alerta → paso a indefinido  
        elif tipo_contrato == "fijo" and primer_plazo is not None and segundo_plazo is None:
            fecha_alerta = primer_plazo - timedelta(days=0) # Alerta el mismo día del término del segundo plazo
            motivo = "Paso a contrato indefinido"
            tipo_alerta = "INDEFINIDO"
            dias_vencimiento = (datetime.datetime.now() - fecha_alerta).days
        
        if fecha_alerta:
            return {
                "fecha_alerta": fecha_alerta.strftime("%Y-%m-%d"),
                "motivo": motivo,
                "tipo_alerta": tipo_alerta,
                "dias_desde_inicio": (datetime.datetime.now() - fecha_activacion).days,
                "dias_vencimiento": dias_vencimiento
            }
        else:
            return None
            
    except ValueError as e:
        print(f"Error procesando fechas para {empleado.get('full_name')}: {e}")
        return None

# %%
def obtener_info_jefe(id_boss, rut_boss, empleados_lista):
    if not id_boss and not rut_boss:
        return None
    
    for empleado in empleados_lista:
        if (id_boss and empleado.get("id") == id_boss) or (rut_boss and empleado.get("rut") == rut_boss):
            return empleado 
    
    return None

#%% Función para generar alertas
def generar_alertas(cursor, conexion):
    """
    Procesa los empleados de la base de datos y genera alertas de contrato.
    """
    # Crear la tabla de alertas si no existe (CON LAS NUEVAS COLUMNAS)
    sql_create_alerts_table = """
    CREATE TABLE IF NOT EXISTS contract_alerts (
        employee_id INT NOT NULL,
        employee_name VARCHAR(255),
        employee_rut VARCHAR(50) PRIMARY KEY,
        employee_role VARCHAR(255),
        employee_start_date DATE,
        employee_contract_type VARCHAR(50),
        boss_name VARCHAR(255),        -- first name of boss
        boss_email VARCHAR(255),      -- email of boss
        boss_of_boss_name VARCHAR(255),     -- first name of boss's boss
        boss_of_boss_email VARCHAR(255),     -- email of boss's boss
        alert_date DATE NOT NULL,
        alert_type VARCHAR(50),
        alert_reason TEXT,
        expiration INT,
        days_since_start INT,
        first_alert_sent BOOLEAN DEFAULT FALSE,
        second_alert_sent BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_employee_id (employee_id),
        INDEX idx_alert_date (alert_date)
    );
    """
    cursor.execute(sql_create_alerts_table)
    print("✅ Tabla 'contract_alerts' creada/verificada exitosamente")
    
    # Consulta para obtener todos los empleados necesarios (sin cambios aquí)
    sql_empleados = """
    SELECT 
        id, person_id, full_name, first_name, rut, email, name_role,
        start_date, contract_type, id_boss, rut_boss,
        active_since, contract_finishing_date_1, contract_finishing_date_2,
        status, payment_method
    FROM employees 
    WHERE status = 'activo'
    """

    cursor.execute(sql_empleados)
    empleados_db = cursor.fetchall()
    
    empleados_lista = []
    columnas = [
        'id', 'person_id', 'full_name', 'first_name', 'rut', 'email', 'name_role',
        'start_date', 'contract_type', 'id_boss', 'rut_boss',
        'active_since', 'contract_finishing_date_1', 'contract_finishing_date_2',
        'status', 'payment_method'
    ]
    
    for empleado_tupla in empleados_db:
        empleado_dict = {}
        for i, columna in enumerate(columnas):
            valor = empleado_tupla[i]
            if isinstance(valor, datetime.date):
                valor = valor.strftime("%Y-%m-%d")
            empleado_dict[columna] = valor
        empleados_lista.append(empleado_dict)
    
    print(f"✅ Cargados {len(empleados_lista)} empleados activos desde la BD")
    
    alertas_insertadas = 0
    empleados_procesados = 0
    errores = 0

    for empleado in empleados_lista:
        empleados_procesados += 1
        alerta = calcular_fecha_alerta(empleado)
        
        if alerta:
            try:
                jefe_directo = obtener_info_jefe(
                    empleado.get("id_boss"), 
                    empleado.get("rut_boss"),
                    empleados_lista
                )
                boss_name = jefe_directo.get("first_name") if jefe_directo else None
                boss_email = jefe_directo.get("email") if jefe_directo else None
                jefe_del_jefe = None
                if jefe_directo:
                    jefe_del_jefe = obtener_info_jefe(
                        jefe_directo.get("id_boss"),
                        jefe_directo.get("rut_boss"),
                        empleados_lista
                    )
                boss_of_boss_name = jefe_del_jefe.get("first_name") if jefe_del_jefe else None
                boss_of_boss_email = jefe_del_jefe.get("email") if jefe_del_jefe else None

                sql_insert = """
                INSERT INTO contract_alerts (
                    employee_id, employee_name, 
                    employee_rut, employee_role, 
                    employee_start_date, employee_contract_type,
                    boss_name, boss_email,
                    boss_of_boss_name, boss_of_boss_email,
                    alert_date, alert_type, 
                    alert_reason, days_since_start,
                    expiration
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    employee_name=VALUES(employee_name),
                    employee_role=VALUES(employee_role),
                    employee_start_date=VALUES(employee_start_date),
                    employee_contract_type=VALUES(employee_contract_type),
                    boss_name=VALUES(boss_name),
                    boss_email=VALUES(boss_email),
                    boss_of_boss_name=VALUES(boss_of_boss_name),
                    boss_of_boss_email=VALUES(boss_of_boss_email),
                    alert_date=VALUES(alert_date),
                    alert_type=VALUES(alert_type),
                    alert_reason=VALUES(alert_reason),
                    days_since_start=VALUES(days_since_start),
                    expiration=VALUES(expiration),
                    first_alert_sent=COALESCE(first_alert_sent, FALSE),
                    second_alert_sent=COALESCE(second_alert_sent, FALSE),
                    updated_at=CURRENT_TIMESTAMP
                """
                
                # Ejecutar inserción (con los nuevos valores)
                cursor.execute(sql_insert, (
                    empleado["id"],
                    empleado["full_name"],
                    empleado["rut"],
                    empleado["name_role"],
                    empleado["start_date"],
                    empleado["contract_type"],
                    boss_name,
                    boss_email,
                    boss_of_boss_name,
                    boss_of_boss_email,
                    alerta["fecha_alerta"],
                    alerta["tipo_alerta"],
                    alerta["motivo"],
                    alerta["dias_desde_inicio"],
                    alerta["dias_vencimiento"]
                ))
                
                alertas_insertadas += 1
                
                if empleados_procesados % 50 == 0:
                    print(f"📊 Procesados: {empleados_procesados}/{len(empleados_lista)} empleados...")
                    
            except Exception as e:
                errores += 1
                print(f"❌ Error insertando alerta para {empleado.get('first_name', 'N/A')}: {e}")

    conexion.commit()
    print(f"""
✅ === PROCESO COMPLETADO ===
👥 Empleados procesados: {empleados_procesados}
🚨 Alertas generadas: {alertas_insertadas}
❌ Errores: {errores}
💾 Cambios guardados en la base de datos
""")
#%% Función principal para ejecutar alertas
def job_generar_alertas():
    """
    Función principal que se ejecutará para generar alertas de contratos.
    """
    print(f"\n🕗 INICIANDO GENERACIÓN DE ALERTAS: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Conectar a MySQL
        print("🚀 Conectando a MySQL...")
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,  
            charset='utf8mb4'
        )
        cursor = conexion.cursor()
        
        print(f"✅ Conectado a MySQL y usando la base: {DB_NAME}")
        
        # Generar nuevas alertas
        generar_alertas(cursor, conexion)
        
        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 GENERACIÓN DE ALERTAS COMPLETADA: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en la generación de alertas: {e}")
        if 'conexion' in locals():
            conexion.close()
    
    # Log del proceso
    # with open("C:/Users/gpavez/Desktop/logs_alertas_contratos.txt", "a", encoding="utf-8") as f:
    #     f.write(f"{datetime.datetime.now()}: Generación de alertas de contratos completada\n")

#%%
if __name__ == "__main__":
    print("SISTEMA DE ALERTAS DE CONTRATOS - MODO PROGRAMADOR DE TAREAS")
    print("="*70)
    
    # Ejecutar SOLO UNA VEZ (para el Programador de Tareas)
    print("📋 Ejecutando generación de alertas programada...")
    job_generar_alertas()
    
    print("✅ Tarea completada. El script finalizará automáticamente.")
    print("La próxima ejecución será programada por Windows.")
    
    sys.exit(0)