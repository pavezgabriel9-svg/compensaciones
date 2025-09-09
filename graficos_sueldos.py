# ====================================================================
# SCRIPT DE ANÁLISIS DE EVOLUCIÓN SALARIAL
# --------------------------------------------------------------------
# Extiende el script de sincronización para conectar a la BD,
# extraer datos de sueldos y generar un gráfico de la evolución.
# ====================================================================

# Importaciones necesarias
import requests
import pymysql
import time
from datetime import datetime
from pymysql.err import IntegrityError
import sys
import pandas as pd
import matplotlib.pyplot as plt


# Configuración BD
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# Funciones del script original (se mantienen intactas)
# ... (obtener_todas_las_areas, crear_tabla_areas, sincronizar_areas, job_sincronizar_areas)

# ====================================================================
# NUEVA LÓGICA DE ANÁLISIS DE SUELDOS
# ====================================================================

def obtener_datos_sueldos(cursor):
    """
    Obtiene los datos de sueldo base y sueldo líquido de la base de datos.
    Retorna dos DataFrames de pandas.
    """
    print("⏳ Obteniendo datos de sueldos desde la base de datos...")
    
    # Consulta para obtener los sueldos líquidos de la tabla historical_settlements
    sql_settlements = """
    SELECT 
        RUT,
        Pay_Period,
        Liquido_a_Pagar
    FROM historical_settlements
    ORDER BY Pay_Period ASC;
    """
    
    # Consulta para obtener los sueldos base de la tabla employees_jobs
    sql_jobs = """
    SELECT
        person_rut,
        start_date,
        base_wage
    FROM employees_jobs
    ORDER BY start_date ASC;
    """
    
    try:
        # Ejecutar las consultas y convertirlas a DataFrame
        cursor.execute(sql_settlements)
        data_settlements = cursor.fetchall()
        column_names_settlements = [desc[0] for desc in cursor.description]
        df_settlements = pd.DataFrame(data_settlements, columns=column_names_settlements)
        
        cursor.execute(sql_jobs)
        data_jobs = cursor.fetchall()
        column_names_jobs = [desc[0] for desc in cursor.description]
        df_jobs = pd.DataFrame(data_jobs, columns=column_names_jobs)
        
        print("✅ Datos obtenidos correctamente.")
        return df_settlements, df_jobs
        
    except Exception as e:
        print(f"❌ Error al obtener datos de sueldos: {e}")
        return pd.DataFrame(), pd.DataFrame()


def procesar_datos_sueldos(df_settlements, df_jobs):
    """
    Combina los DataFrames de sueldos para alinear el sueldo base y el líquido.
    """
    print("🔄 Procesando y uniendo los datos...")
    
    if df_settlements.empty or df_jobs.empty:
        print("Datos de origen vacíos. No se puede procesar.")
        return pd.DataFrame()
    
    # Renombrar columnas para facilitar la unión
    df_jobs = df_jobs.rename(columns={'person_rut': 'RUT'})
    
    # La corrección clave: convertir 'start_date' del DataFrame de jobs a datetime
    df_jobs['start_date'] = pd.to_datetime(df_jobs['start_date'])
    
    # Unir los sueldos líquidos con los sueldos base por RUT
    df_combined = pd.merge(df_settlements, df_jobs, on='RUT', how='left')
    
    # Convertir las columnas de fecha a formato datetime
    df_combined['Pay_Period'] = pd.to_datetime(df_combined['Pay_Period'])
    
    # Asegurar que el sueldo base correcto se use para cada período de pago
    # El sueldo base de un trabajo es válido desde su start_date
    df_combined = df_combined.sort_values(by=['RUT', 'Pay_Period'])
    df_combined['sueldo_base'] = None
    
    for rut in df_combined['RUT'].unique():
        df_persona = df_combined[df_combined['RUT'] == rut].copy()
        
        # Obtener los cambios de sueldo base para esta persona
        cambios_sueldo = df_jobs[df_jobs['RUT'] == rut].sort_values(by='start_date')
        
        if cambios_sueldo.empty:
            continue
            
        # Asignar el sueldo base a cada período de pago
        for idx, row in df_persona.iterrows():
            fecha_pago = row['Pay_Period']
            # Buscar el sueldo base más reciente antes o en la fecha de pago
            salarios_anteriores = cambios_sueldo[cambios_sueldo['start_date'] <= fecha_pago]['base_wage']
            
            # Corrección para el error: verificar si hay salarios antes de acceder a iloc[-1]
            if not salarios_anteriores.empty:
                salario = salarios_anteriores.iloc[-1]
                df_combined.loc[idx, 'sueldo_base'] = salario
            else:
                df_combined.loc[idx, 'sueldo_base'] = None # Opcional: asignar None si no se encuentra un sueldo
    
    # Limpiar columnas temporales y convertir a tipo numérico
    df_combined['sueldo_base'] = pd.to_numeric(df_combined['sueldo_base'], errors='coerce')
    df_combined['Liquido_a_Pagar'] = pd.to_numeric(df_combined['Liquido_a_Pagar'], errors='coerce')
    
    print("✅ Datos procesados y listos para graficar.")
    return df_combined


def graficar_evolucion_sueldo(df, rut_persona):
    """
    Filtra los datos por RUT y genera un gráfico de la evolución de sueldo.
    """
    df_persona = df[df['RUT'] == rut_persona].copy()
    
    if df_persona.empty:
        print(f"❌ No se encontraron datos para el RUT: {rut_persona}")
        return

    # Crear el gráfico
    plt.figure(figsize=(12, 7))
    plt.plot(df_persona['Pay_Period'], df_persona['sueldo_base'], marker='o', linestyle='-', label='Sueldo Base')
    plt.plot(df_persona['Pay_Period'], df_persona['Liquido_a_Pagar'], marker='o', linestyle='-', label='Sueldo Líquido')

    # Añadir títulos y etiquetas
    plt.title(f'Evolución del Sueldo de la persona con RUT: {rut_persona}', fontsize=16, fontweight='bold')
    plt.xlabel('Fecha de Pago', fontsize=12)
    plt.ylabel('Monto ($)', fontsize=12)
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout() # Ajusta el diseño para que las etiquetas no se corten
    plt.show()

def job_analisis_sueldos(rut_a_analizar):
    """
    Función principal para el análisis de sueldos.
    """
    print("\n" + "="*60)
    print("INICIANDO ANÁLISIS DE EVOLUCIÓN SALARIAL")
    print("="*60)
    print(f"⏰ Fecha/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. Conectar a la base de datos
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
        
        # 2. Obtener y procesar datos
        df_settlements, df_jobs = obtener_datos_sueldos(cursor)
        df_final = procesar_datos_sueldos(df_settlements, df_jobs)
        
        # 3. Generar el gráfico si hay datos
        if not df_final.empty:
            graficar_evolucion_sueldo(df_final, rut_a_analizar)
        else:
            print("No se pudo generar el gráfico debido a la falta de datos.")
        
        # 4. Cerrar conexión
        cursor.close()
        conexion.close()
        print("✅ Conexión cerrada correctamente.")
        print(f"🎉 ANÁLISIS COMPLETADO: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ Error general en el análisis: {e}")
        if 'conexion' in locals():
            conexion.close()
    
    # El archivo de log ya no se crea aquí, se mantiene la estructura original.

# ========================================
# EJECUCIÓN
# ========================================

if __name__ == "__main__":
    print("SISTEMA DE ANÁLISIS DE SUELDOS")
    print("="*70)
    
    # Definir el RUT que deseas analizar
    rut_a_analizar = '19.420.469-8'
    
    # Ejecutar el análisis de sueldos
    job_analisis_sueldos(rut_a_analizar)
    
    print("✅ Tarea de análisis completada. El script finalizará automáticamente.")
    sys.exit(0)

