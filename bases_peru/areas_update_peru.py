#importaciones necesarias
import requests
import pymysql
import time
from datetime import datetime
from pymysql.err import IntegrityError
import sys

# Configuración API
URL_AREAS = 'https://cramer.buk.cl/api/v1/chile/organization/areas/?status=both'
TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

# Configuración BD - windows
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# Configuración BD - mac
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "conexion_buk"

#%%
def obtener_todas_las_areas():
    """
    Obtiene todas las áreas desde la API con paginación y las devuelve filtradas.
    """
    headers = {"auth_token": TOKEN}
    areas_filtradas = []
    url_actual = URL_AREAS
    pagina_actual = 1
    
    print(f"🚀 Comenzando obtención de áreas: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        while url_actual:
            print(f"   📄 Procesando página {pagina_actual}...")
            
            respuesta = requests.get(url_actual, headers=headers, timeout=30)
            respuesta.raise_for_status()
            
            respuesta_api = respuesta.json()
            areas_pagina = respuesta_api['data']
            pagination_info = respuesta_api['pagination']
            
            # Filtrar cada área de esta página
            for area_completa in areas_pagina:
                area_filtrada = {
                    "id": area_completa.get("id"),
                    "name": area_completa.get("name"),
                    "address": area_completa.get("address"),
                    "first_level_id": area_completa.get("first_level_id"),
                    "first_level_name": area_completa.get("first_level_name"),
                    "second_level_id": area_completa.get("second_level_id"),
                    "second_level_name": area_completa.get("second_level_name"),
                    "cost_center": area_completa.get("cost_center"),
                    "status": area_completa.get("status"),
                    "city": area_completa.get("city"),
                }
                areas_filtradas.append(area_filtrada)
            
            print(f"   ✅ Página {pagina_actual}: {len(areas_pagina)} áreas procesadas")
            
            # Obtener la URL de la siguiente página
            url_actual = pagination_info.get('next')
            pagina_actual += 1
            
            # Pausa para no sobrecargar la API
            time.sleep(0.5)
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error en petición API: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error procesando áreas: {e}")
        return []
        
    print(f"✅ Total áreas obtenidas: {len(areas_filtradas)}")
    return areas_filtradas

# %%
def crear_tabla_areas(cursor):
    """
    Crea la tabla de áreas si no existe.
    """
    print("🔧 Verificando/creando tabla areas...")
    
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS areas (
        id INT PRIMARY KEY,
        name VARCHAR(255),
        address TEXT,
        first_level_id INT,
        first_level_name VARCHAR(255),
        second_level_id INT,
        second_level_name VARCHAR(255),
        cost_center VARCHAR(100),
        status VARCHAR(50),
        city VARCHAR(100),
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
    
    try:
        cursor.execute(sql_create_table)
        print("✅ Tabla 'areas' verificada/creada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False

# %%
def sincronizar_areas(areas_datos, cursor, conexion):
    """
    Sincroniza las áreas en la base de datos de manera más eficiente.
    """
    print("Iniciando sincronización de áreas...")
    
    contador_insertados = 0
    contador_actualizados = 0
    errores = 0
    
    sql_upsert = """
    INSERT INTO areas (
        id, name, address, first_level_id, first_level_name,
        second_level_id, second_level_name, cost_center, status, city
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        name=VALUES(name),
        address=VALUES(address),
        first_level_id=VALUES(first_level_id),
        first_level_name=VALUES(first_level_name),
        second_level_id=VALUES(second_level_id),
        second_level_name=VALUES(second_level_name),
        cost_center=VALUES(cost_center),
        status=VALUES(status),
        city=VALUES(city)
    """
    
    for i, area in enumerate(areas_datos):
        try:
            values = (
                area.get("id"),
                area.get("name"),
                area.get("address"),
                area.get("first_level_id"),
                area.get("first_level_name"),
                area.get("second_level_id"),
                area.get("second_level_name"),
                area.get("cost_center"),
                area.get("status"),
                area.get("city")
            )
            
            # Ejecutamos la operación de inserción/actualización
            cursor.execute(sql_upsert, values)
            
            # Usamos cursor.rowcount para saber si fue una inserción (1) o actualización (2)
            if cursor.rowcount == 1:
                contador_insertados += 1
            elif cursor.rowcount == 2:
                contador_actualizados += 1
            
            # Mostrar progreso cada 25 registros
            if (i + 1) % 25 == 0:
                print(f"   📝 Procesadas {i + 1}/{len(areas_datos)} áreas...")
                
        except IntegrityError as error:
            print(f"   ⚠️ Error de integridad (posiblemente ID duplicado): {error}")
            errores += 1
        except Exception as error:
            print(f"   ⚠️ Error inesperado procesando área {area.get('id', 'N/A')}: {error}")
            errores += 1
    
    # Confirmar cambios
    conexion.commit()
    
    print(f"Sincronización completada:")
    print(f"Áreas insertadas: {contador_insertados}")
    print(f"Áreas actualizadas: {contador_actualizados}")
    
    if errores > 0:
        print(f"   ⚠️ Errores: {errores}")
    
    return contador_insertados + contador_actualizados

def job_sincronizar_areas():
    """
    Función principal para la sincronización automática de áreas.
    """
    print("\n" + "="*60)
    print("INICIANDO SINCRONIZACIÓN DE ÁREAS")
    print("="*60)
    print(f"⏰ Fecha/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Obtener áreas desde la API
        areas_datos = obtener_todas_las_areas()
        
        if not areas_datos:
            print("❌ No se obtuvieron datos de áreas. Cancelando sincronización.")
            return
        
        # 2. Conectar a la base de datos
        print("Conectando a la base de datos...")
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )
        cursor = conexion.cursor()
        print("✅ Conexión establecida correctamente")
        
        # 3. Crear tabla si no existe
        if not crear_tabla_areas(cursor):
            print(" Error en la tabla. Cancelando sincronización.")
            return
        
        # 4. Sincronizar datos
        total_procesados = sincronizar_areas(areas_datos, cursor, conexion)
        print(f"Total áreas procesadas (insertadas/actualizadas): {total_procesados}")
        
        # 5. Cerrar conexión
        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 SINCRONIZACIÓN COMPLETADA: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en la sincronización: {e}")
        if 'conexion' in locals():
            conexion.close()
    
    with open('C:/Users/gpavez/Desktop/sync_log.txt', 'a') as f:
        f.write(f"{datetime.now()}: Sincronización completada\n")

# ========================================
# EJECUCIÓN Y SCHEDULER
# ========================================

if __name__ == "__main__":
    print("SISTEMA DE SINCRONIZACIÓN DE ÁREAS - MODO PROGRAMADOR DE TAREAS")
    print("="*70)
    
    # Ejecutar SOLO UNA VEZ (para el Programador de Tareas)
    print("🔍 Ejecutando sincronización programada...")
    job_sincronizar_areas()
    
    print("✅ Tarea completada. El script finalizará automáticamente.")
    print("La próxima ejecución será programada por Windows.")

    sys.exit(0)