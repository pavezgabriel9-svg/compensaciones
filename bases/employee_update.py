# %%
import requests
import os
import pymysql
import time
import json
import datetime
from datetime import timedelta
import sys


# Configuración API
URL = "https://cramer.buk.cl/api/v1/chile/employees"
TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

# Configuración BD - windows
DB_HOST = "10.254.32.110"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# # Configuración BD - mac
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "conexion_buk"


# %%
def obtener_todos_los_empleados_filtrados():
    """Sincroniza empleados y genera alertas (ejecución programada por Windows)."""
    headers = {"auth_token": TOKEN}
    empleados_filtrados = []
    url_actual = URL
    pagina_actual = 1
    
    print("🚀 Comenzando la obtención de todos los empleados con paginación...")
    
    while url_actual:
        print(f"📄 Obteniendo página {pagina_actual}...")
        
        try:
            respuesta = requests.get(url_actual, headers=headers)
            respuesta.raise_for_status()
            
            respuesta_api = respuesta.json()
            empleados_pagina = respuesta_api['data']
            pagination_info = respuesta_api['pagination']
            
            # Filtrar cada empleado de esta página
            for empleado_completo in empleados_pagina:
                empleado_filtrado = {
                #información Personal
                "person_id": empleado_completo.get("person_id"),
                "id": empleado_completo.get("id"),
                "full_name": empleado_completo.get("full_name"),
                "rut": empleado_completo.get("rut"),
                "email": empleado_completo.get("email"),
                "personal_email": empleado_completo.get("personal_email"),
                "address": empleado_completo.get("address"),
                "street": empleado_completo.get("street"),
                "street_number": empleado_completo.get("street_number"),
                "city": empleado_completo.get("city"),
                "province": empleado_completo.get("province"),
                "district": empleado_completo.get("district"),
                "region": empleado_completo.get("region"),
                "phone": empleado_completo.get("phone"),
                "gender": empleado_completo.get("gender"),
                "birthday": empleado_completo.get("birthday"),
                "university": empleado_completo.get("university"),
                "degree": empleado_completo.get("degree"),
                "bank": empleado_completo.get("bank"),
                "account_type": empleado_completo.get("account_type"),
                "account_number": empleado_completo.get("account_number"),
                "nationality": empleado_completo.get("nationality"),
                "civil_status": empleado_completo.get("civil_status"),
                "health_company": empleado_completo.get("health_company"),
                "pension_regime": empleado_completo.get("pension_regime"),
                "pension_fund": empleado_completo.get("pension_fund"),
                "active_until": empleado_completo.get("active_until"),
                "afc": empleado_completo.get("afc"),
                "retired": empleado_completo.get("retired"),
                "retirement_regime": empleado_completo.get("retirement_regime"),
                #Información Laboral
                "active_since": empleado_completo.get("active_since"),
                "status": empleado_completo.get("status"),
                "start_date": empleado_completo.get("current_job", {}).get("start_date"),
                "end_date": empleado_completo.get("current_job", {}).get("end_date"),
                "termination_reason": empleado_completo.get("termination_reason"),
                "payment_method": empleado_completo.get("payment_method"),
                "id_boss": empleado_completo.get("current_job", {}).get("boss", {}).get("id"),
                "rut_boss": empleado_completo.get("current_job", {}).get("boss", {}).get("rut"),
                "base_wage": empleado_completo.get("current_job", {}).get("base_wage",),
                "contract_type": empleado_completo.get("current_job", {}).get("contract_type"),
                "contract_finishing_date_1": empleado_completo.get("current_job", {}).get("contract_finishing_date_1"),
                "contract_finishing_date_2": empleado_completo.get("current_job", {}).get("contract_finishing_date_2"),
                'name_role': empleado_completo.get("current_job", {}).get("role", {}).get("name"),
                'area_id': empleado_completo.get("current_job", {}).get("area_id"),
                "cost_center": empleado_completo.get("current_job", {}).get("cost_center"),
                }
                empleados_filtrados.append(empleado_filtrado)
            
            print(f"✅ Página {pagina_actual}: {len(empleados_pagina)} empleados procesados")
            print(f"📊 Total acumulado: {len(empleados_filtrados)} empleados filtrados")
            
            # Obtener la URL de la siguiente página
            url_actual = pagination_info.get('next')
            pagina_actual += 1
            
            # Pequeña pausa para no sobrecargar la API
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en la petición: {e}")
            break
            
    print(f"🎉 ¡Paginación completada! Total de empleados filtrados: {len(empleados_filtrados)}")
    return empleados_filtrados

# %%
def limpiar_duplicados_existentes(cursor):
    """Limpia los duplicados existentes antes de aplicar la nueva estructura"""
    print("🧹 Limpiando duplicados existentes...")
    
    # Crear tabla temporal con registros únicos
    sql_temp = """
    CREATE TEMPORARY TABLE temp_employees AS
    SELECT DISTINCT * FROM employees
    """
    
    try:
        cursor.execute(sql_temp)
        
        # Vaciar tabla original
        cursor.execute("DELETE FROM employees")
        
        # Insertar registros únicos de vuelta
        cursor.execute("INSERT INTO employees SELECT * FROM temp_employees")
        
        # Eliminar tabla temporal
        cursor.execute("DROP TEMPORARY TABLE temp_employees")
        
        print("✅ Duplicados eliminados exitosamente")
        
    except Exception as e:
        print(f"⚠️ Error limpiando duplicados: {e}")

# %%
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
            fecha_alerta = fecha_activacion + timedelta(days=14)
            motivo = "Segundo plazo de contratación"
            tipo_alerta = "SEGUNDO_PLAZO"
        
        # Segunda alerta → paso a indefinido  
        elif tipo_contrato == "fijo" and primer_plazo is not None and segundo_plazo is None:
            fecha_alerta = fecha_activacion + timedelta(days=76)
            motivo = "Paso a contrato indefinido"
            tipo_alerta = "INDEFINIDO"
        
        if fecha_alerta:
            return {
                "fecha_alerta": fecha_alerta.strftime("%Y-%m-%d"),
                "motivo": motivo,
                "tipo_alerta": tipo_alerta,
                "dias_desde_inicio": (datetime.datetime.now() - fecha_activacion).days,
                "requiere_accion": fecha_alerta <= datetime.datetime.now(),
                "urgente": (fecha_alerta - datetime.datetime.now()).days <= 7 if fecha_alerta > datetime.datetime.now() else True
            }
        else:
            return None
            
    except ValueError as e:
        print(f"Error procesando fechas para {empleado.get('full_name')}: {e}")
        return None

# %%
def obtener_info_jefe(id_boss, rut_boss, empleados_lista):
    """
    Busca la información del jefe en la lista de empleados.
    """
    if not id_boss and not rut_boss:
        return None, None, None
    
    for empleado in empleados_lista:
        # Buscar por ID primero, luego por RUT
        if (id_boss and empleado.get("id") == id_boss) or (rut_boss and empleado.get("rut") == rut_boss):
            return (
                empleado.get("full_name"),
                empleado.get("email"),
                empleado.get("rut")
            )
    
    return None, None, None

# %%
def generar_alertas(cursor, conexion):
    """
    Procesa los empleados de la base de datos y genera alertas de contrato.
    """
    print("🔄 === PROCESANDO ALERTAS DE CONTRATOS ===\n")
    
    # Crear la tabla de alertas si no existe
    sql_create_alerts_table = """
    CREATE TABLE IF NOT EXISTS contract_alerts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        employee_id INT NOT NULL,
        employee_name VARCHAR(255),
        employee_rut VARCHAR(50),
        employee_area_name VARCHAR(255),
        employee_role VARCHAR(255),
        employee_start_date DATE,
        employee_contract_type VARCHAR(50),
        boss_name VARCHAR(255),
        boss_email VARCHAR(255),
        alert_date DATE NOT NULL,
        alert_type VARCHAR(50),
        alert_reason TEXT,
        days_since_start INT,
        requires_action BOOLEAN DEFAULT FALSE,
        is_urgent BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        notes TEXT,
        INDEX idx_employee_id (employee_id),
        INDEX idx_alert_date (alert_date),
        INDEX idx_requires_action (requires_action),
        INDEX idx_is_urgent (is_urgent),
        INDEX idx_processed (processed)
    );
    """
    cursor.execute(sql_create_alerts_table)
    print("✅ Tabla 'contract_alerts' creada/verificada exitosamente")
    
    # Consulta para obtener todos los empleados necesarios
    sql_empleados = """
    SELECT 
        id, person_id, full_name, rut, email, area_id, name_role,
        start_date, contract_type, base_wage, id_boss, rut_boss,
        active_since, contract_finishing_date_1, contract_finishing_date_2,
        status, payment_method
    FROM employees 
    WHERE status = 'activo'
    """
    
    cursor.execute(sql_empleados)
    empleados_db = cursor.fetchall()
    
    # Convertir a lista de diccionarios para facilitar el manejo
    empleados_lista = []
    columnas = [
        'id', 'person_id', 'full_name', 'rut', 'email', 'area_id', 'name_role',
        'start_date', 'contract_type', 'base_wage', 'id_boss', 'rut_boss',
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
                # Obtener información del jefe
                boss_name, boss_email, boss_rut_real = obtener_info_jefe(
                    empleado.get("id_boss"), 
                    empleado.get("rut_boss"), 
                    empleados_lista
                )
                
                # Preparar datos para insertar
                sql_insert = """
                INSERT INTO contract_alerts (
                    employee_id, employee_name, employee_rut, employee_area_name, employee_role, employee_start_date, 
                    employee_contract_type,
                    boss_name, boss_email,
                    alert_date, alert_type, alert_reason, days_since_start,
                    requires_action, is_urgent
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                # Ejecutar inserción
                cursor.execute(sql_insert, (
                    empleado["id"],
                    empleado["full_name"],
                    empleado["rut"],
                    # Nota: La función obtener_nombre_area fue eliminada para simplificar
                    "N/A", # Placeholder para area_name
                    empleado["name_role"],
                    empleado["start_date"],
                    empleado["contract_type"],
                    boss_name,
                    boss_email,
                    alerta["fecha_alerta"],
                    alerta["tipo_alerta"],
                    alerta["motivo"],
                    alerta["dias_desde_inicio"],
                    alerta["requiere_accion"],
                    alerta["urgente"]
                ))
                
                alertas_insertadas += 1
                
                if empleados_procesados % 50 == 0:
                    print(f"📊 Procesados: {empleados_procesados}/{len(empleados_lista)} empleados...")
                    
            except Exception as e:
                errores += 1
                print(f"❌ Error insertando alerta para {empleado.get('full_name', 'N/A')}: {e}")

    conexion.commit()
    print(f"""
✅ === PROCESO COMPLETADO ===
👥 Empleados procesados: {empleados_procesados}
🚨 Alertas generadas: {alertas_insertadas}
❌ Errores: {errores}
💾 Cambios guardados en la base de datos
""")


# %%
def job_sincronizar_empleados():
    """Esta función se ejecutará todos los días a las 8:00 AM"""
    print(f"\n🕗 INICIANDO SINCRONIZACIÓN PROGRAMADA: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Obtener empleados de la API
        empleados_filtrados = obtener_todos_los_empleados_filtrados()

        # Conectar a MySQL
        print("🚀 Conectando a MySQL...")
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conexion.cursor()

        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        print(f"✅ Conectado a MySQL y usando la base: {DB_NAME}")

        print("🚀 Creando tabla employees con clave primaria...")
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS employees (
            person_id INT UNIQUE,  
            full_name VARCHAR(255),
            rut VARCHAR(50) PRIMARY KEY, -- Clave primaria
            id INT, 
            email VARCHAR(255),
            personal_email VARCHAR(255),
            address TEXT,
            street VARCHAR(255),
            street_number VARCHAR(50),
            city VARCHAR(100),
            province VARCHAR(100),
            district VARCHAR(100),
            region VARCHAR(100),
            phone VARCHAR(50),
            gender VARCHAR(50),
            birthday DATE,
            university VARCHAR(255),
            degree VARCHAR(255),
            bank VARCHAR(100),
            account_type VARCHAR(50),
            account_number VARCHAR(50),
            nationality VARCHAR(100),
            civil_status VARCHAR(50),
            health_company VARCHAR(255),
            pension_regime VARCHAR(255),
            pension_fund VARCHAR(255),
            active_until DATE,
            afc VARCHAR(50),
            retired BOOLEAN,
            retirement_regime VARCHAR(255),
            active_since DATE,
            status VARCHAR(50),
            start_date DATE,
            end_date DATE,
            termination_reason VARCHAR(255),
            payment_method VARCHAR(50),
            id_boss INT,
            rut_boss VARCHAR(50),
            base_wage INT,
            contract_type VARCHAR(50),
            contract_finishing_date_1 DATE,
            contract_finishing_date_2 DATE,
            name_role VARCHAR(255),
            area_id INT,
            cost_center VARCHAR(255),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- TIMESTAMP DE ACTUALIZACIÓN
        );
        """
        cursor.execute(sql_create_table)
        print("✅ Tabla 'employees' creada exitosamente con clave primaria")

        # Limpiar duplicados existentes si la tabla ya tenía datos
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        if count > 0:
            limpiar_duplicados_existentes(cursor)

        # Insertar empleados con ON DUPLICATE KEY UPDATE mejorado
        print("🚀 Insertando/Actualizando empleados en la tabla SQL...")
        contador = 0
        actualizaciones = 0
        errores = 0

        for e in empleados_filtrados:
            try:
                sql = """
                INSERT INTO employees (
                person_id, id, full_name, rut, email, personal_email, active_since, 
                status, payment_method, id_boss, rut_boss, contract_type, start_date, 
                end_date, contract_finishing_date_1, contract_finishing_date_2, area_id, cost_center,
                address, street, street_number, city, province, district, region, phone, 
                gender, birthday, university, degree, bank, account_type, 
                account_number, nationality, civil_status, health_company, 
                pension_regime, pension_fund, active_until, termination_reason, afc, retired, 
                retirement_regime, base_wage, name_role
                )
                VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    -- CAMPOS INMUTABLES (NO SE ACTUALIZAN)
                    -- rut NO se actualiza (inmutable)
                    
                    -- CAMPOS QUE SÍ SE ACTUALIZAN
                    person_id=VALUES(person_id),
                    full_name=VALUES(full_name),
                    email=VALUES(email),
                    personal_email=VALUES(personal_email),
                    active_since=VALUES(active_since),
                    status=VALUES(status),
                    payment_method=VALUES(payment_method),
                    id_boss=VALUES(id_boss),
                    rut_boss=VALUES(rut_boss),
                    contract_type=VALUES(contract_type),
                    start_date=VALUES(start_date),
                    end_date=VALUES(end_date),
                    contract_finishing_date_1=VALUES(contract_finishing_date_1),
                    contract_finishing_date_2=VALUES(contract_finishing_date_2),
                    area_id=VALUES(area_id),
                    cost_center=VALUES(cost_center),
                    address=VALUES(address),
                    street=VALUES(street),
                    street_number=VALUES(street_number),
                    city=VALUES(city),
                    province=VALUES(province),
                    district=VALUES(district),
                    region=VALUES(region),
                    phone=VALUES(phone),
                    gender=VALUES(gender),
                    birthday=VALUES(birthday),
                    university=VALUES(university),
                    degree=VALUES(degree),
                    bank=VALUES(bank),
                    account_type=VALUES(account_type),
                    account_number=VALUES(account_number),
                    nationality=VALUES(nationality),
                    civil_status=VALUES(civil_status),
                    health_company=VALUES(health_company),
                    pension_regime=VALUES(pension_regime),
                    pension_fund=VALUES(pension_fund),
                    active_until=VALUES(active_until),
                    termination_reason=VALUES(termination_reason),
                    afc=VALUES(afc),
                    retired=VALUES(retired),
                    retirement_regime=VALUES(retirement_regime),
                    base_wage=VALUES(base_wage),
                    name_role=VALUES(name_role)
                """
                
                values = (
                    e.get("person_id"),
                    e.get("id"),
                    e.get("full_name"),
                    e.get("rut"),
                    e.get("email"),
                    e.get("personal_email"),
                    e.get("active_since"),
                    e.get("status"),
                    e.get("payment_method"),
                    e.get("id_boss"),
                    e.get("rut_boss"),
                    e.get("contract_type"),
                    e.get("start_date"),
                    e.get("end_date"),
                    e.get("contract_finishing_date_1"),
                    e.get("contract_finishing_date_2"),
                    e.get("area_id"),
                    e.get("cost_center"),
                    e.get("address"),
                    e.get("street"),
                    e.get("street_number"),
                    e.get("city"),
                    e.get("province"),
                    e.get("district"),
                    e.get("region"),
                    e.get("phone"),
                    e.get("gender"),
                    e.get("birthday"),
                    e.get("university"),
                    e.get("degree"),
                    e.get("bank"),
                    e.get("account_type"),
                    e.get("account_number"),
                    e.get("nationality"),
                    e.get("civil_status"),
                    e.get("health_company"),
                    e.get("pension_regime"),
                    e.get("pension_fund"),
                    e.get("active_until"),
                    e.get("termination_reason"),
                    e.get("afc"),
                    e.get("retired"),
                    e.get("retirement_regime"),
                    e.get("base_wage"),
                    e.get("name_role") 
                )
                
                cursor.execute(sql, values)
                
                # Verificar si fue INSERT o UPDATE
                if cursor.rowcount == 1:
                    contador += 1
                elif cursor.rowcount == 2:  # MySQL devuelve 2 cuando hace UPDATE
                    actualizaciones += 1
                
                # Mostrar progreso cada 100 registros
                if (contador + actualizaciones) % 100 == 0:
                    print(f"📝 Procesados {contador + actualizaciones} empleados (Nuevos: {contador}, Actualizados: {actualizaciones})...")      
            except Exception as error:
                print(f"⚠️ Error procesando empleado {e.get('id', 'N/A')}: {error}")
                errores += 1

        conexion.commit()
        print(f"✅ Procesamiento completado:")
        print(f"   📝 Nuevos registros: {contador}")
        print(f"   🔄 Registros actualizados: {actualizaciones}")
        if errores > 0:
            print(f"   ⚠️ Errores: {errores}")
            
        # Generar alertas después de actualizar los datos
        generar_alertas(cursor, conexion)

        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 SINCRONIZACIÓN COMPLETADA: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en la sincronización: {e}")

    with open("C:/Users/gpavez/Desktop/logs_sync_empleados.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()}: Sincronización de empleados completada\n")
        
#%%
if __name__ == "__main__":
    print("SISTEMA DE SINCRONIZACIÓN DE empleados - MODO PROGRAMADOR DE TAREAS")
    print("="*70)
    
    # Ejecutar SOLO UNA VEZ (para el Programador de Tareas)
    print("🔍 Ejecutando sincronización programada...")
    job_sincronizar_empleados()
    
    print("✅ Tarea completada. El script finalizará automáticamente.")
    print("La próxima ejecución será programada por Windows.")

    sys.exit(0)