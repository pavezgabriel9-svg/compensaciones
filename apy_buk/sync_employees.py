# %%
import requests
import os
import pymysql
import time
import json
import schedule

# Configuración API
URL = "https://cramer.buk.cl/api/v1/chile/employees"
TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

# Configuración BD
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# %%
def obtener_todos_los_empleados_filtrados():
    """
    Obtiene todos los empleados desde la API con paginación y los devuelve filtrados
    con solo los campos necesarios.
    """
    headers = {"auth_token": TOKEN}
    empleados_filtrados = []
    url_actual = URL
    pagina_actual = 1
    
    print("🚀 Comenzando la obtención de todos los empleados con paginación...")
    
    while url_actual:  # Limitar a 100 páginas para evitar bucles infinitos
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

        print("🚀 Creando tabla employees completa si no existe...")
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS employees (
            person_id INT,
            id INT,
            full_name VARCHAR(255),
            rut VARCHAR(50),
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
            cost_center VARCHAR(255)
        );
        """
        cursor.execute(sql_create_table)
        print("✅ Tabla 'employees' creada exitosamente")

        # Insertar empleados
        print("🚀 Insertando TODOS los empleados en la tabla SQL...")
        contador = 0
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
                    person_id=VALUES(person_id),
                    full_name=VALUES(full_name),
                    rut=VALUES(rut),
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
                if len(values) != 45:
                    print(f"⚠️ Error: empleado {e.get('id', 'N/A')} tiene {len(values)} valores, se esperaban 45.")
                    print("Valores:", values)
                    continue 
                cursor.execute(sql, values)
                contador += 1
                
                # Mostrar progreso cada 100 registros
                if contador % 100 == 0:
                    print(f"📝 Procesados {contador} empleados...")      
            except Exception as error:
                print(f"⚠️ Error insertando empleado {e.get('id', 'N/A')}: {error}")
                errores += 1

        conexion.commit()
        print(f"✅ {contador} registros insertados/actualizados en MySQL.")
        if errores > 0:
            print(f"⚠️ Se produjeron {errores} errores durante la inserción.")

        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 SINCRONIZACIÓN COMPLETADA: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en la sincronización: {e}")

# %%
# PROGRAMACIÓN AUTOMÁTICA
schedule.every().day.at("09:40").do(job_sincronizar_empleados)

print("📅 SCHEDULER ACTIVO - Se ejecutará todos los días a las 09:40 AM")
print("👉 Para testing: cambia '09:40' por la hora actual +1 minuto")
print("🛑 Presiona Ctrl+C para detener el scheduler")
print("⏰ Próxima ejecución programada:", schedule.next_run())

# Mantener el script corriendo
while True:
    schedule.run_pending()
    time.sleep(30)  # Revisar cada 30 segundos