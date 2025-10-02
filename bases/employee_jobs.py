# %%
import requests
import pymysql
import time
import datetime
from datetime import datetime
import sys

# Configuración API
URL = "https://cramer.buk.cl/api/v1/chile/employees"
TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

# Configuración BD - Windows
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# Configuración BD - Mac
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "conexion_buk"

# %%
def obtener_historial_laboral_completo():
    """
    Obtiene todos los registros de historial laboral (jobs) de cada persona,
    incluyendo el trabajo actual, y los devuelve en una lista plana.
    """
    headers = {"auth_token": TOKEN}
    historial_laboral = []
    url_actual = URL
    pagina_actual = 1
    
    print("🚀 Comenzando la obtención del historial laboral completo...")
    
    while url_actual:
        print(f"📄 Obteniendo página {pagina_actual}...")
        
        try:
            respuesta = requests.get(url_actual, headers=headers)
            respuesta.raise_for_status()
            
            respuesta_api = respuesta.json()
            data_pagina = respuesta_api['data']
            pagination_info = respuesta_api['pagination']
            
            # Recorrer cada persona en la página
            for persona in data_pagina:
                person_id = persona.get("person_id")
                person_rut = persona.get("rut")
                
                # Obtener el trabajo actual y el historial de trabajos
                all_jobs = []
                if persona.get("current_job"):
                    all_jobs.append(persona.get("current_job"))
                if persona.get("jobs"):
                    all_jobs.extend(persona.get("jobs"))
                
                # Procesar cada trabajo de la persona
                for job in all_jobs:
                    if job:
                        job_record = {
                            "job_id": job.get("id"),
                            "person_id": person_id,
                            "person_rut": person_rut,
                            "start_date": job.get("start_date"),
                            "end_date": job.get("end_date"),
                            "base_wage": job.get("base_wage"),
                            "role_name": job.get("role", {}).get("name"),
                            "boss_id": job.get("boss", {}).get("id"),
                            "boss_rut": job.get("boss", {}).get("rut"),
                        }
                        historial_laboral.append(job_record)

            print(f"✅ Página {pagina_actual}: {len(data_pagina)} personas procesadas.")
            
            url_actual = pagination_info.get('next')
            pagina_actual += 1
            
            # Pausa para no sobrecargar la API
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en la petición: {e}")
            break
            
    print(f"🎉 ¡Paginación completada! Total de registros de trabajo: {len(historial_laboral)}")
    # Eliminar duplicados en caso de que 'current_job' esté en el array 'jobs'
    registros_unicos = {rec['job_id']: rec for rec in historial_laboral}.values()
    print(f"📝 Total de registros únicos: {len(registros_unicos)}")
    return list(registros_unicos)

# %%
def job_sincronizar_historial_laboral():
    """Esta función crea y sincroniza la tabla de historial de trabajos."""
    print(f"\n🕗 INICIANDO SINCRONIZACIÓN DE HISTORIAL LABORAL: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Obtener el historial de trabajos de la API
        historial_laboral = obtener_historial_laboral_completo()

        # 2. Conectar a MySQL
        print("🚀 Conectando a MySQL...")
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conexion.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        print(f"✅ Conectado a MySQL y usando la base: {DB_NAME}")

        # 3. Crear la tabla `job_history` si no existe
        print("🚀 Creando/Verificando tabla 'job_history'...")
        sql_create_table = """
        CREATE TABLE IF NOT EXISTS job_history  (
            job_id INT PRIMARY KEY,
            person_id INT,
            person_rut VARCHAR(50),
            start_date DATE,
            end_date DATE,
            base_wage INT,
            role_name VARCHAR(255),
            boss_id INT,
            boss_rut VARCHAR(50),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
        """
        cursor.execute(sql_create_table)
        print("✅ Tabla 'employees_jobs' creada exitosamente.")

        # 4. Insertar/actualizar datos en la nueva tabla
        print("🚀 Insertando/Actualizando datos en 'employees_jobs'...")
        contador = 0
        actualizaciones = 0
        errores = 0

        for job in historial_laboral:
            try:
                sql = """
                INSERT INTO job_history  (
                    job_id, person_id, person_rut, start_date, end_date, base_wage, 
                    historical_role, boss_id, boss_rut
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    person_id=VALUES(person_id), person_rut=VALUES(person_rut),
                    start_date=VALUES(start_date), end_date=VALUES(end_date), 
                    base_wage=VALUES(base_wage), historical_role=VALUES(historical_role),
                    boss_id=VALUES(boss_id), boss_rut=VALUES(boss_rut);
                """
                values = (
                    job.get("job_id"), job.get("person_id"), job.get("person_rut"), 
                    job.get("start_date"), job.get("end_date"), job.get("base_wage"),
                    job.get("role_name"), job.get("boss_id"), job.get("boss_rut")
                )
                
                cursor.execute(sql, values)
                
                if cursor.rowcount == 1:
                    contador += 1
                elif cursor.rowcount == 2:
                    actualizaciones += 1
                
                if (contador + actualizaciones) % 100 == 0:
                    print(f"📝 Procesados {contador + actualizaciones} registros...")      
            except Exception as error:
                print(f"⚠️ Error procesando registro de trabajo {job.get('job_id', 'N/A')}: {error}")
                errores += 1

        conexion.commit()
        print(f"""
✅ === PROCESO COMPLETADO ===
📋 Registros procesados: {len(historial_laboral)}
➕ Nuevos registros: {contador}
🔄 Registros actualizados: {actualizaciones}
❌ Errores: {errores}
💾 Cambios guardados en la base de datos
""")
        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 SINCRONIZACIÓN COMPLETADA: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en la sincronización: {e}")
    
    with open('C:/Users/gpavez/Desktop/logs_sync_jobs_employees.txt', 'a') as f:
        f.write(f"{datetime.now()}: Sincronización completada\n")

# %%
if __name__ == "__main__":
    print("SISTEMA DE SINCRONIZACIÓN DE ÁREAS - MODO PROGRAMADOR DE TAREAS")
    print("="*70)
    print("🔍 Ejecutando sincronización programada...")
    job_sincronizar_historial_laboral()

    print("✅ Tarea completada. El script finalizará automáticamente.")
    print("La próxima ejecución será programada por Windows.")

    sys.exit(0)