import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
import json
from dateutil.relativedelta import relativedelta
import pymysql
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.types import (
    Integer, String, Float, Date, Boolean
)
import os
import signal
import sys

# ==== CONFIGURACIÓN BD ====
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"
DB_TABLE = "historical_settlements_complete" 

def get_db_engine():
    """Crea conexión SQLAlchemy para escritura en la BD"""
    conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(conn_str)

def create_unique_constraint():
    """
    🔹 NUEVO: Crea constraint único para evitar duplicados
    """
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            # Verificar si ya existe la constraint
            result = conn.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.table_constraints 
                WHERE table_schema = '{DB_NAME}' 
                AND table_name = '{DB_TABLE}' 
                AND constraint_name = 'uniq_emp_period'
            """)
            
            if result.fetchone()[0] == 0:
                # Crear constraint único
                conn.execute(f"""
                    ALTER TABLE {DB_TABLE} 
                    ADD CONSTRAINT uniq_emp_period 
                    UNIQUE KEY (ID_Empleado, Año, Mes)
                """)
                print("✅ Constraint único creado: uniq_emp_period (ID_Empleado, Año, Mes)")
            else:
                print("ℹ️ Constraint único ya existe")
    except Exception as e:
        print(f"⚠️ Error creando constraint (puede ser normal si ya existe): {e}")

def save_to_db_upsert(df, table_name=DB_TABLE):
    """
    🔹 NUEVO: Inserta datos en BD con UPSERT (evita duplicados)
    Si la tabla no existe, la crea con esquema fijo.
    Agrega columna created_at (solo fecha).
    """
    if df is None or df.empty:
        print("⚠️ No hay datos para insertar en la BD.")
        return

    engine = get_db_engine()
    insp = inspect(engine)
    metadata = MetaData()

    # 🔹 Agregar columna `created_at` solo con la fecha
    df = df.copy()
    df["created_at"] = datetime.now().date()

    # 🔹 ESQUEMA EXPANDIDO para capturar evolución completa
    schema = {
        "ID_Empleado": Integer(),
        "ID_Persona": Integer(),
        "RUT": String(20),
        "Nombre": String(255),
        "Género": String(20),
        "Fecha_Nacimiento": Date(),
        "Fecha_Activacion": Date(),
        
        # 🔹 DATOS DEL PERÍODO ESPECÍFICO (lo que tenía vigente en esa fecha)
        "Cargo_Periodo": String(255),           # Cargo vigente en este período
        "ID_Rol_Periodo": Integer(),            # ID del rol vigente
        "Familia_Rol_Periodo": String(255),    # Familia del rol vigente
        "Sueldo_Base_Teorico": Float(),        # base_wage del contrato vigente
        "ID_Area_Periodo": Integer(),          # Área vigente en este período
        "Nombre_Area_Periodo": String(255),    # 🔹 NUEVO: Nombre del área
        "Tipo_Contrato_Periodo": String(50),   # Tipo contrato vigente
        "Centro_Costo_Periodo": String(255),   # Centro costo vigente
        "Horas_Semanales_Periodo": Integer(),  # Horas vigentes
        "ID_Jefe_Periodo": Integer(),          # 🔹 NUEVO: ID del jefe vigente
        "Nombre_Jefe_Periodo": String(255),    # 🔹 NUEVO: Nombre del jefe vigente
        
        # 🔹 DATOS DE LIQUIDACIÓN
        "Sueldo_Base_Liquidacion": Float(),
        "Período": String(10),
        "Año": Integer(),
        "Mes": Integer(),
        "Edad": Float(),
        "Rango_de_Edad": String(20),
        "Años_de_Servicio": Float(),
        "Rango_de_Antigüedad": String(30),
        "Estado": String(50),
        "Tiene_Liquidación": Boolean(),
        "Liquidación_ID": Integer(),
        "Días_Trabajados": Integer(),
        "Días_No_Trabajados": Integer(),
        "Ingreso_Bruto": Float(),
        "Ingreso_Neto": Float(),
        "Ingreso_AFP": Float(),
        "Ingreso_IPS": Float(),
        "Total_Ingresos_Imponibles": Float(),
        "Total_Ingresos_No_Imponibles": Float(),
        "Total_Descuentos_Legales": Float(),
        "Total_Otros_Descuentos": Float(),
        "Líquido_a_Pagar": Float(),
        "Base_Imponible": Float(),
        "Cerrada": Boolean(),
        "created_at": Date()
    }

    try:
        # Si la tabla no existe → la crea
        if not insp.has_table(table_name):
            print(f"ℹ️ La tabla {table_name} no existe. Creándola con esquema expandido...")
            df.head(0).to_sql(table_name, con=engine, if_exists="replace", index=False, dtype=schema)
            
            # Crear constraint único después de crear la tabla
            create_unique_constraint()

        # 🔹 UPSERT: Usar REPLACE INTO para evitar duplicados
        with engine.connect() as conn:
            # Preparar columnas para REPLACE INTO
            columns = list(df.columns)
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f"`{col}`" for col in columns])
            
            replace_query = f"""
                REPLACE INTO {table_name} ({columns_str}) 
                VALUES ({placeholders})
            """
            
            # Insertar fila por fila (más seguro para REPLACE)
            inserted_count = 0
            for _, row in df.iterrows():
                try:
                    conn.execute(replace_query, tuple(row))
                    inserted_count += 1
                except Exception as e:
                    print(f"⚠️ Error insertando fila: {e}")
                    continue
            
            conn.commit()
            print(f"✅ {inserted_count}/{len(df)} registros insertados/actualizados en tabla {table_name}")
            
    except Exception as e:
        print(f"❌ Error insertando en BD: {e}")

def save_checkpoint(period_label):
    """
    🔹 NUEVO: Guarda checkpoint del último período procesado
    """
    try:
        with open("checkpoint_historial.txt", "w") as f:
            f.write(period_label)
        print(f"📍 Checkpoint guardado: {period_label}")
    except Exception as e:
        print(f"⚠️ Error guardando checkpoint: {e}")

def load_checkpoint():
    """
    🔹 NUEVO: Carga checkpoint del último período procesado
    """
    try:
        if os.path.exists("checkpoint_historial.txt"):
            with open("checkpoint_historial.txt", "r") as f:
                checkpoint = f.read().strip()
            print(f"📍 Checkpoint encontrado: {checkpoint}")
            return checkpoint
    except Exception as e:
        print(f"⚠️ Error cargando checkpoint: {e}")
    return None

def signal_handler(signum, frame):
    """
    🔹 NUEVO: Maneja Ctrl+C para guardar progreso antes de salir
    """
    print("\n🛑 Interrupción detectada (Ctrl+C)")
    print("💾 El progreso ya está guardado en la BD por períodos")
    print("🔄 Para continuar, ejecuta de nuevo el script (usará checkpoint automático)")
    sys.exit(0)

def get_all_employees_data(base_url, token):
    """
    Obtiene todos los empleados activos actuales paginando a través de la API
    """
    all_data = []
    page = 1

    while True:
        url = f"{base_url}?page_size=100&page={page}"
        headers = {"auth_token": token}
    
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
            current_data = data.get('data', [])
            if not current_data or len(current_data) == 0:
                break
            
            all_data.extend(current_data)
        
            if len(current_data) < 100:
                break
            
            page += 1
        
        except requests.exceptions.RequestException as e:
            print(f"Error en la página {page}: {e}")
            break

    return all_data

def get_all_liquidaciones_data(base_url, token, date_param):
    """
    Obtiene todas las liquidaciones para una fecha específica paginando a través de la API
    """
    all_data = []
    page = 1

    while True:
        url = f"{base_url}?date={date_param}&page_size=100&page={page}"
        headers = {"auth_token": token}
    
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
            current_data = data.get('data', [])
            if not current_data or len(current_data) == 0:
                break
            
            all_data.extend(current_data)
        
            if len(current_data) < 100:
                break
            
            page += 1
        
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo liquidaciones para {date_param}, página {page}: {e}")
            break

    return all_data

def extract_sueldo_base_from_liquidacion(liquidacion_data):
    """
    Extrae el sueldo base específico de la liquidación desde lines_settlement
    """
    if not liquidacion_data or 'lines_settlement' not in liquidacion_data:
        return None

    lines = liquidacion_data.get('lines_settlement', [])

    for line in lines:
        # Buscar la línea que corresponde al sueldo base
        if (line.get('type') == 'haber' and
            line.get('code') == 'wage' and
            line.get('name') == 'Sueldo Base'):
            return line.get('amount')

    return None

def find_job_data_for_period(employee_data, period_year, period_month):
    """
    🔹 FUNCIÓN EXPANDIDA: Encuentra TODOS los datos del job vigente para un período específico
    Retorna: base_wage, role_info, area_id, boss_info, contract_type, etc.
    """
    if not employee_data:
        return {}

    # Fecha del período que estamos analizando (primer día del mes)
    period_date = datetime(period_year, period_month, 1).date()

    # Primero revisar current_job si aplica
    current_job = employee_data.get('current_job', {})
    if current_job:
        start_date_str = current_job.get('start_date')
        end_date_str = current_job.get('end_date')
    
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
            # Si el período está dentro del rango del current_job
            if start_date <= period_date and (end_date is None or period_date <= end_date):
                return extract_job_details(current_job)

    # Si no está en current_job, buscar en jobs históricos
    jobs = employee_data.get('jobs', [])
    for job in jobs:
        start_date_str = job.get('start_date')
        end_date_str = job.get('end_date')
    
        if not start_date_str:
            continue
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
        # Si el período está dentro del rango de este job
        if start_date <= period_date and (end_date is None or period_date <= end_date):
            return extract_job_details(job)

    return {}

def extract_job_details(job_data):
    """
    🔹 NUEVA FUNCIÓN: Extrae todos los detalles relevantes de un job
    """
    details = {}
    
    # Datos básicos del job
    details['base_wage'] = job_data.get('base_wage')
    details['area_id'] = job_data.get('area_id')
    details['contract_type'] = job_data.get('contract_type')
    details['cost_center'] = job_data.get('cost_center')
    details['weekly_hours'] = job_data.get('weekly_hours')
    
    # 🔹 Datos del rol
    role = job_data.get('role', {})
    if role:
        details['role_name'] = role.get('name')
        details['role_id'] = role.get('id')
        
        # Familia del rol
        role_family = role.get('role_family', {})
        if role_family:
            details['role_family_name'] = role_family.get('name')
    
    # 🔹 Datos del área
    area = job_data.get('area', {})
    if area:
        details['area_name'] = area.get('name')
    
    # 🔹 Datos del jefe
    boss = job_data.get('boss', {})
    if boss:
        details['boss_id'] = boss.get('id')
        details['boss_name'] = boss.get('full_name')
    
    return details

def generate_all_liquidation_periods():
    """
    🔹 NUEVA FUNCIÓN: Genera TODOS los períodos mensuales desde enero 2019 hasta agosto 2025
    """
    periods = []
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2025, 8, 31)  # Hasta agosto 2025
    
    current_date = start_date
    while current_date <= end_date:
        periods.append({
            'month': current_date.month,
            'year': current_date.year,
            'period_label': f"{current_date.strftime('%m')}-{current_date.year}",
            'date_param': f"01-{current_date.strftime('%m')}-{current_date.year}"
        })
        current_date += relativedelta(months=1)  # 🔹 CADA MES, no cada 3
    
    return periods

def calculate_years_from_date(start_date, reference_date):
    """
    Calcula años desde una fecha hasta una fecha de referencia
    """
    if pd.isna(start_date) or start_date is None:
        return None

    try:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
    
        if isinstance(reference_date, str):
            reference_date = pd.to_datetime(reference_date).date()
        elif isinstance(reference_date, datetime):
            reference_date = reference_date.date()
    
        years = (reference_date - start_date).days / 365.25
        return round(years, 1)
    except:
        return None

def process_employee_for_period(employee_data, period_year, period_month):
    """
    🔹 FUNCIÓN COMPLETAMENTE NUEVA: Procesa un empleado para un período específico
    Extrae tanto datos fijos como datos variables (cargo, jefe, área) vigentes en esa fecha
    """
    processed = {}

    # 🔹 DATOS BÁSICOS (no cambian)
    processed['ID_Empleado'] = employee_data.get('id')
    processed['ID_Persona'] = employee_data.get('person_id')
    processed['RUT'] = employee_data.get('rut')
    processed['Nombre'] = employee_data.get('full_name')
    processed['Género'] = employee_data.get('gender')
    processed['Fecha_Nacimiento'] = employee_data.get('birthday')
    processed['Fecha_Activacion'] = employee_data.get('active_since')

    # 🔹 DATOS VARIABLES (específicos del período)
    job_details = find_job_data_for_period(employee_data, period_year, period_month)
    
    # Mapear datos del job vigente en este período
    processed['Sueldo_Base_Teorico'] = job_details.get('base_wage')
    processed['Cargo_Periodo'] = job_details.get('role_name')
    processed['ID_Rol_Periodo'] = job_details.get('role_id')
    processed['Familia_Rol_Periodo'] = job_details.get('role_family_name')
    processed['ID_Area_Periodo'] = job_details.get('area_id')
    processed['Nombre_Area_Periodo'] = job_details.get('area_name')
    processed['Tipo_Contrato_Periodo'] = job_details.get('contract_type')
    processed['Centro_Costo_Periodo'] = job_details.get('cost_center')
    processed['Horas_Semanales_Periodo'] = job_details.get('weekly_hours')
    processed['ID_Jefe_Periodo'] = job_details.get('boss_id')
    processed['Nombre_Jefe_Periodo'] = job_details.get('boss_name')

    # 🔹 DATOS DEL PERÍODO
    processed['Período'] = f"{period_month:02d}-{period_year}"
    processed['Mes'] = period_month
    processed['Año'] = period_year

    # 🔹 CALCULAR EDAD Y ANTIGÜEDAD para este período específico
    period_date = datetime(period_year, period_month, 1).date()

    if processed.get('Fecha_Nacimiento'):
        processed['Edad'] = calculate_years_from_date(
            processed['Fecha_Nacimiento'], period_date
        )

    if processed.get('Fecha_Activacion'):
        processed['Años_de_Servicio'] = calculate_years_from_date(
            processed['Fecha_Activacion'], period_date
        )

    return processed

def was_employee_active_in_period(employee_data, period_year, period_month):
    """
    🔹 NUEVA FUNCIÓN: Verifica si un empleado estaba activo en un período específico
    """
    if not employee_data:
        return False
    
    period_date = datetime(period_year, period_month, 1).date()
    
    # Verificar fecha de activación
    active_since_str = employee_data.get('active_since')
    if active_since_str:
        active_since = datetime.strptime(active_since_str, '%Y-%m-%d').date()
        if period_date < active_since:
            return False  # Aún no había ingresado
    
    # Verificar si tenía algún contrato vigente en ese período
    job_details = find_job_data_for_period(employee_data, period_year, period_month)
    return bool(job_details)  # Si encontró job details, estaba activo

def get_complete_historical_data_safe(employees_url, liquidaciones_url, token):
    """
    🔹 FUNCIÓN PRINCIPAL OPTIMIZADA Y SEGURA: 
    1. Obtiene empleados UNA SOLA VEZ
    2. Para cada período de liquidación, procesa los datos de cada empleado
    3. 🔹 GUARDA AUTOMÁTICAMENTE CADA PERÍODO EN BD
    4. 🔹 MANEJA CHECKPOINTS PARA REANUDAR
    """
    # 🔹 Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    # 🔹 1. OBTENER EMPLEADOS UNA SOLA VEZ (optimización)
    print("🔄 Obteniendo lista completa de empleados...")
    employees_data = get_all_employees_data(employees_url, token)
    
    if not employees_data:
        print("❌ No se pudieron obtener empleados")
        return []

    # Filtrar empleados activos y excluir IDs específicos
    excluded_ids = [4804, 9386]
    filtered_employees = [emp for emp in employees_data 
                         if emp.get('status', '').lower() in ['active', 'activo'] and
                            emp.get('id') not in excluded_ids and 
                            emp.get('person_id') not in excluded_ids]
    
    print(f"✅ {len(filtered_employees)} empleados activos obtenidos")

    # 🔹 2. GENERAR TODOS LOS PERÍODOS MENSUALES
    periods = generate_all_liquidation_periods()
    print(f"📅 Se procesarán {len(periods)} períodos mensuales (ene-2019 a ago-2025)")

    # 🔹 3. VERIFICAR CHECKPOINT PARA REANUDAR
    checkpoint = load_checkpoint()
    skip_until_checkpoint = checkpoint is not None
    
    if checkpoint:
        print(f"🔄 Reanudando desde checkpoint: {checkpoint}")

    total_records_processed = 0

    # 🔹 4. PARA CADA PERÍODO, OBTENER LIQUIDACIONES Y PROCESAR EMPLEADOS
    try:
        for i, period in enumerate(periods):
            # 🔹 SKIP períodos ya procesados según checkpoint
            if skip_until_checkpoint:
                if period['period_label'] == checkpoint:
                    skip_until_checkpoint = False
                    print(f"📍 Checkpoint alcanzado, continuando desde: {period['period_label']}")
                    continue
                else:
                    print(f"⏭️ Saltando período ya procesado: {period['period_label']}")
                    continue
            
            print(f"🔄 Procesando período {i+1}/{len(periods)}: {period['period_label']}")
            
            # Obtener liquidaciones para este período
            liquidaciones_data = get_all_liquidaciones_data(liquidaciones_url, token, period['date_param'])
            
            # Crear diccionario de liquidaciones por employee_id
            liquidaciones_dict = {}
            if liquidaciones_data:
                for liq in liquidaciones_data:
                    emp_id = liq.get('employee_id')
                    if emp_id:
                        liquidaciones_dict[emp_id] = liq
            
            print(f"   📊 Liquidaciones encontradas: {len(liquidaciones_dict)}")
            
            # 🔹 5. PROCESAR CADA EMPLEADO PARA ESTE PERÍODO
            period_records = []
            for employee in filtered_employees:
                emp_id = employee['id']
                
                # Procesar datos del empleado para este período específico
                employee_record = process_employee_for_period(employee, period['year'], period['month'])
                
                # Buscar liquidación para este empleado en este período
                liquidacion = liquidaciones_dict.get(emp_id)
                
                if liquidacion:
                    # 🔹 AGREGAR DATOS DE LIQUIDACIÓN
                    employee_record['Liquidación_ID'] = liquidacion.get('liquidacion_id')
                    employee_record['Días_Trabajados'] = liquidacion.get('worked_days')
                    employee_record['Días_No_Trabajados'] = liquidacion.get('noworked_days')
                    employee_record['Ingreso_Bruto'] = liquidacion.get('income_gross')
                    employee_record['Ingreso_Neto'] = liquidacion.get('income_net')
                    employee_record['Ingreso_AFP'] = liquidacion.get('income_afp')
                    employee_record['Ingreso_IPS'] = liquidacion.get('income_ips')
                    employee_record['Total_Ingresos_Imponibles'] = liquidacion.get('total_income_taxable')
                    employee_record['Total_Ingresos_No_Imponibles'] = liquidacion.get('total_income_notaxable')
                    employee_record['Total_Descuentos_Legales'] = liquidacion.get('total_legal_discounts')
                    employee_record['Total_Otros_Descuentos'] = liquidacion.get('total_other_discounts')
                    employee_record['Líquido_a_Pagar'] = liquidacion.get('liquid_reach')
                    employee_record['Base_Imponible'] = liquidacion.get('taxable_base')
                    employee_record['Cerrada'] = liquidacion.get('closed')
                    employee_record['Tiene_Liquidación'] = True
                    
                    # Extraer sueldo base específico de esta liquidación
                    employee_record['Sueldo_Base_Liquidacion'] = extract_sueldo_base_from_liquidacion(liquidacion)
                    
                    employee_record['Estado'] = 'Activo con liquidación'
                else:
                    # 🔹 SIN LIQUIDACIÓN: Solo agregar si el empleado estaba activo en ese período
                    if was_employee_active_in_period(employee, period['year'], period['month']):
                        # Llenar campos de liquidación con None
                        liquidacion_fields = [
                            'Liquidación_ID', 'Días_Trabajados', 'Días_No_Trabajados',
                            'Ingreso_Bruto', 'Ingreso_Neto', 'Ingreso_AFP', 'Ingreso_IPS',
                            'Total_Ingresos_Imponibles', 'Total_Ingresos_No_Imponibles',
                            'Total_Descuentos_Legales', 'Total_Otros_Descuentos',
                            'Líquido_a_Pagar', 'Base_Imponible', 'Cerrada', 'Sueldo_Base_Liquidacion'
                        ]
                        for field in liquidacion_fields:
                            employee_record[field] = None
                        employee_record['Tiene_Liquidación'] = False
                        employee_record['Estado'] = 'Activo sin liquidación'
                    else:
                        # Si no estaba activo, no agregar registro para este período
                        continue
                
                period_records.append(employee_record)

            # 🔹 6. CONVERTIR A DATAFRAME Y CALCULAR RANGOS
            if period_records:
                df_period = pd.DataFrame(period_records)
                
                # Calcular rangos de edad
                def age_range(age):
                    if pd.isna(age):
                        return "No disponible"
                    elif age < 25:
                        return "18-24"
                    elif age < 35:
                        return "25-34"
                    elif age < 45:
                        return "35-44"
                    elif age < 55:
                        return "45-54"
                    elif age < 65:
                        return "55-64"
                    else:
                        return "65+"
                
                if 'Edad' in df_period.columns:
                    df_period['Rango_de_Edad'] = df_period['Edad'].apply(age_range)
                else:
                    df_period['Rango_de_Edad'] = "No disponible"

                # Calcular rangos de antigüedad
                def service_range(years):
                    if pd.isna(years):
                        return "No disponible"
                    elif years < 1:
                        return "Menos de 1 año"
                    elif years < 3:
                        return "1-3 años"
                    elif years < 5:
                        return "3-5 años"
                    elif years < 10:
                        return "5-10 años"
                    else:
                        return "Más de 10 años"
                
                if 'Años_de_Servicio' in df_period.columns:
                    df_period['Rango_de_Antigüedad'] = df_period['Años_de_Servicio'].apply(service_range)
                else:
                    df_period['Rango_de_Antigüedad'] = "No disponible"

                # 🔹 7. GUARDAR INMEDIATAMENTE EN BD (CLAVE PARA NO PERDER DATOS)
                save_to_db_upsert(df_period)
                
                # 🔹 8. GUARDAR RESPALDO CSV OPCIONAL
                csv_filename = f"historial_parcial_{period['period_label']}.csv"
                df_period.to_csv(csv_filename, index=False)
                
                # 🔹 9. ACTUALIZAR CHECKPOINT
                save_checkpoint(period['period_label'])
                
                total_records_processed += len(df_period)
                print(f"   ✅ {len(df_period)} registros guardados en BD y CSV")
            else:
                print(f"   ⚠️ No hay registros para este período")
                # Aún así, guardar checkpoint para no repetir
                save_checkpoint(period['period_label'])

    except KeyboardInterrupt:
        print(f"\n🛑 Proceso interrumpido por el usuario")
        print(f"💾 Progreso guardado hasta el período actual")
        print(f"📊 Total registros procesados: {total_records_processed:,}")
        print(f"🔄 Para continuar, ejecuta de nuevo el script")
        return total_records_processed
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        print(f"💾 Progreso guardado hasta el período actual")
        print(f"📊 Total registros procesados: {total_records_processed:,}")
        return total_records_processed

    print(f"🎉 Proceso completado exitosamente!")
    print(f"📊 Total registros procesados: {total_records_processed:,}")
    
    # 🔹 10. LIMPIAR CHECKPOINT AL COMPLETAR
    if os.path.exists("checkpoint_historial.txt"):
        os.remove("checkpoint_historial.txt")
        print("🧹 Checkpoint limpiado (proceso completado)")

    return total_records_processed

def create_final_excel_from_db(output_file='historial_completo_desde_bd.xlsx'):
    """
    🔹 NUEVA FUNCIÓN: Crea Excel final leyendo desde la BD
    """
    print("📊 Creando Excel final desde la base de datos...")
    
    try:
        engine = get_db_engine()
        
        # Leer todos los datos de la BD
        query = f"SELECT * FROM {DB_TABLE} ORDER BY ID_Empleado, Año, Mes"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            print("⚠️ No hay datos en la base de datos")
            return None
        
        print(f"📊 {len(df):,} registros leídos desde BD")
        
        # 🔹 CREAR MÚLTIPLES HOJAS EN EXCEL
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            # 🔹 HOJA 1: Historial completo
            df.to_excel(writer, sheet_name='Historial_Completo', index=False)
            
            # 🔹 HOJA 2: Solo registros con liquidación
            df_with_liq = df[df['Tiene_Liquidación'] == True].copy()
            if len(df_with_liq) > 0:
                df_with_liq.to_excel(writer, sheet_name='Solo_con_Liquidaciones', index=False)
            
            # 🔹 HOJA 3: Evolución de cargos por empleado
            df_evolution = create_employee_evolution_summary(df)
            if len(df_evolution) > 0:
                df_evolution.to_excel(writer, sheet_name='Evolucion_Empleados', index=False)
            
            # 🔹 HOJA 4: Cambios detectados (cargo, jefe, área)
            df_changes = detect_employee_changes(df)
            if len(df_changes) > 0:
                df_changes.to_excel(writer, sheet_name='Cambios_Detectados', index=False)
            
            # 🔹 HOJA 5: Estadísticas por período
            df_period_stats = create_period_statistics(df)
            if len(df_period_stats) > 0:
                df_period_stats.to_excel(writer, sheet_name='Estadisticas_Periodo', index=False)
            
            # 🔹 HOJA 6: Resumen por empleado
            df_employee_summary = create_employee_summary(df)
            if len(df_employee_summary) > 0:
                df_employee_summary.to_excel(writer, sheet_name='Resumen_Empleados', index=False)

        print(f"📁 Excel final guardado en '{output_file}'")
        print(f"📊 Total de registros: {len(df):,}")
        print(f"👥 Empleados únicos: {df['ID_Empleado'].nunique():,}")
        print(f"📅 Períodos procesados: {df['Período'].nunique()}")
        
        if 'Tiene_Liquidación' in df.columns:
            total_with_liq = df['Tiene_Liquidación'].sum()
            total_records = len(df)
            print(f"💰 Registros con liquidación: {total_with_liq:,}/{total_records:,} ({total_with_liq/total_records*100:.1f}%)")

        return df
        
    except Exception as e:
        print(f"❌ Error creando Excel desde BD: {e}")
        return None

def create_employee_evolution_summary(df):
    """
    🔹 NUEVA FUNCIÓN: Crea resumen de evolución por empleado
    """
    evolution_data = []
    
    for emp_id in df['ID_Empleado'].unique():
        emp_data = df[df['ID_Empleado'] == emp_id].sort_values(['Año', 'Mes'])
        
        if len(emp_data) == 0:
            continue
            
        first_record = emp_data.iloc[0]
        last_record = emp_data.iloc[-1]
        
        # Contar cambios únicos
        unique_cargos = emp_data['Cargo_Periodo'].dropna().nunique()
        unique_areas = emp_data['ID_Area_Periodo'].dropna().nunique()
        unique_jefes = emp_data['ID_Jefe_Periodo'].dropna().nunique()
        
        # Evolución salarial
        sueldos = emp_data['Sueldo_Base_Teorico'].dropna()
        
        evolution = {
            'ID_Empleado': emp_id,
            'Nombre': first_record.get('Nombre'),
            'RUT': first_record.get('RUT'),
            'Primer_Período': first_record.get('Período'),
            'Último_Período': last_record.get('Período'),
            'Total_Períodos_Registrados': len(emp_data),
            'Períodos_con_Liquidación': emp_data['Tiene_Liquidación'].sum(),
            
            # 🔹 EVOLUCIÓN DE CARGOS
            'Primer_Cargo': first_record.get('Cargo_Periodo'),
            'Último_Cargo': last_record.get('Cargo_Periodo'),
            'Total_Cargos_Diferentes': unique_cargos,
            'Cambió_de_Cargo': 'Sí' if unique_cargos > 1 else 'No',
            
            # 🔹 EVOLUCIÓN DE ÁREAS
            'Primera_Área_ID': first_record.get('ID_Area_Periodo'),
            'Última_Área_ID': last_record.get('ID_Area_Periodo'),
            'Total_Áreas_Diferentes': unique_areas,
            'Cambió_de_Área': 'Sí' if unique_areas > 1 else 'No',
            
            # 🔹 EVOLUCIÓN DE JEFATURAS
            'Primer_Jefe': first_record.get('Nombre_Jefe_Periodo'),
            'Último_Jefe': last_record.get('Nombre_Jefe_Periodo'),
            'Total_Jefes_Diferentes': unique_jefes,
            'Cambió_de_Jefe': 'Sí' if unique_jefes > 1 else 'No',
            
            # 🔹 EVOLUCIÓN SALARIAL
            'Primer_Sueldo': sueldos.iloc[0] if len(sueldos) > 0 else None,
            'Último_Sueldo': sueldos.iloc[-1] if len(sueldos) > 0 else None,
            'Variación_Sueldo_Absoluta': (sueldos.iloc[-1] - sueldos.iloc[0]) if len(sueldos) > 1 else None,
            'Variación_Sueldo_Porcentual': round(
                (sueldos.iloc[-1] / sueldos.iloc[0] - 1) * 100, 1
            ) if len(sueldos) > 1 and sueldos.iloc[0] > 0 else None,
        }
        
        evolution_data.append(evolution)
    
    return pd.DataFrame(evolution_data)

def detect_employee_changes(df):
    """
    🔹 NUEVA FUNCIÓN: Detecta cambios específicos (cargo, jefe, área) entre períodos
    """
    changes_data = []
    
    for emp_id in df['ID_Empleado'].unique():
        emp_data = df[df['ID_Empleado'] == emp_id].sort_values(['Año', 'Mes'])
        
        if len(emp_data) <= 1:
            continue
        
        # Comparar período a período
        for i in range(1, len(emp_data)):
            current = emp_data.iloc[i]
            previous = emp_data.iloc[i-1]
            
            changes_detected = []
            
            # 🔹 DETECTAR CAMBIO DE CARGO
            if (pd.notna(current.get('Cargo_Periodo')) and 
                pd.notna(previous.get('Cargo_Periodo')) and
                current.get('Cargo_Periodo') != previous.get('Cargo_Periodo')):
                changes_detected.append({
                    'Tipo_Cambio': 'Cargo',
                    'Valor_Anterior': previous.get('Cargo_Periodo'),
                    'Valor_Nuevo': current.get('Cargo_Periodo')
                })
            
            # 🔹 DETECTAR CAMBIO DE JEFE
            if (pd.notna(current.get('Nombre_Jefe_Periodo')) and 
                pd.notna(previous.get('Nombre_Jefe_Periodo')) and
                current.get('Nombre_Jefe_Periodo') != previous.get('Nombre_Jefe_Periodo')):
                changes_detected.append({
                    'Tipo_Cambio': 'Jefe',
                    'Valor_Anterior': previous.get('Nombre_Jefe_Periodo'),
                    'Valor_Nuevo': current.get('Nombre_Jefe_Periodo')
                })
            
            # 🔹 DETECTAR CAMBIO DE ÁREA
            if (pd.notna(current.get('ID_Area_Periodo')) and 
                pd.notna(previous.get('ID_Area_Periodo')) and
                current.get('ID_Area_Periodo') != previous.get('ID_Area_Periodo')):
                changes_detected.append({
                    'Tipo_Cambio': 'Área',
                    'Valor_Anterior': f"{previous.get('Nombre_Area_Periodo')} (ID: {previous.get('ID_Area_Periodo')})",
                    'Valor_Nuevo': f"{current.get('Nombre_Area_Periodo')} (ID: {current.get('ID_Area_Periodo')})"
                })
            
            # 🔹 DETECTAR CAMBIO SALARIAL SIGNIFICATIVO (>5%)
            if (pd.notna(current.get('Sueldo_Base_Teorico')) and 
                pd.notna(previous.get('Sueldo_Base_Teorico')) and
                previous.get('Sueldo_Base_Teorico') > 0):
                
                variacion_pct = (current.get('Sueldo_Base_Teorico') / previous.get('Sueldo_Base_Teorico') - 1) * 100
                if abs(variacion_pct) >= 5:  # Cambio >= 5%
                    changes_detected.append({
                        'Tipo_Cambio': 'Sueldo',
                        'Valor_Anterior': f"${previous.get('Sueldo_Base_Teorico'):,.0f}",
                        'Valor_Nuevo': f"${current.get('Sueldo_Base_Teorico'):,.0f} ({variacion_pct:+.1f}%)"
                    })
            
            # 🔹 REGISTRAR CAMBIOS DETECTADOS
            for change in changes_detected:
                change_record = {
                    'ID_Empleado': emp_id,
                    'Nombre': current.get('Nombre'),
                    'RUT': current.get('RUT'),
                    'Período_Anterior': previous.get('Período'),
                    'Período_Actual': current.get('Período'),
                    'Tipo_Cambio': change['Tipo_Cambio'],
                    'Valor_Anterior': change['Valor_Anterior'],
                    'Valor_Nuevo': change['Valor_Nuevo'],
                    'Fecha_Cambio': f"{current.get('Año')}-{current.get('Mes'):02d}-01"
                }
                changes_data.append(change_record)
    
    return pd.DataFrame(changes_data)

def create_period_statistics(df):
    """
    🔹 NUEVA FUNCIÓN: Crea estadísticas por período
    """
    if len(df) == 0:
        return pd.DataFrame()
    
    period_stats = df.groupby('Período').agg({
        'ID_Empleado': 'count',
        'Tiene_Liquidación': 'sum',
        'Sueldo_Base_Teorico': ['mean', 'median', 'min', 'max'],
        'Sueldo_Base_Liquidacion': ['mean', 'median'],
        'Líquido_a_Pagar': ['count', 'mean', 'median', 'sum'],
        'Ingreso_Bruto': ['mean', 'median'],
        'Días_Trabajados': 'mean'
    }).round(0)

    # Aplanar columnas multinivel
    period_stats.columns = ['_'.join(col).strip() for col in period_stats.columns]
    period_stats = period_stats.reset_index()

    # Agregar porcentaje de empleados con liquidación
    period_stats['Porcentaje_con_Liquidación'] = round(
        (period_stats['Tiene_Liquidación_sum'] / period_stats['ID_Empleado_count']) * 100, 1
    )

    return period_stats

def create_employee_summary(df):
    """
    🔹 NUEVA FUNCIÓN: Crea resumen detallado por empleado
    """
    summary_data = []
    
    for emp_id in df['ID_Empleado'].unique():
        emp_data = df[df['ID_Empleado'] == emp_id].sort_values(['Año', 'Mes'])
        
        if len(emp_data) == 0:
            continue
            
        latest_record = emp_data.iloc[-1]
        first_record = emp_data.iloc[0]
        
        # Datos con liquidación
        with_liquidacion = emp_data[emp_data['Tiene_Liquidación'] == True]
        
        summary = {
            'ID_Empleado': emp_id,
            'Nombre': latest_record.get('Nombre'),
            'RUT': latest_record.get('RUT'),
            'Fecha_Activacion': first_record.get('Fecha_Activacion'),
            
            # 🔹 ESTADO ACTUAL
            'Cargo_Actual': latest_record.get('Cargo_Periodo'),
            'Área_Actual': latest_record.get('Nombre_Area_Periodo'),
            'Jefe_Actual': latest_record.get('Nombre_Jefe_Periodo'),
            'Sueldo_Actual': latest_record.get('Sueldo_Base_Teorico'),
            
            # 🔹 ESTADÍSTICAS GENERALES
            'Primer_Período': first_record.get('Período'),
            'Último_Período': latest_record.get('Período'),
            'Total_Períodos_Registrados': len(emp_data),
            'Períodos_con_Liquidación': len(with_liquidacion),
            'Porcentaje_Períodos_con_Liquidación': round(len(with_liquidacion) / len(emp_data) * 100, 1),
            
            # 🔹 EVOLUCIÓN
            'Cargos_Diferentes': emp_data['Cargo_Periodo'].dropna().nunique(),
            'Áreas_Diferentes': emp_data['ID_Area_Periodo'].dropna().nunique(),
            'Jefes_Diferentes': emp_data['ID_Jefe_Periodo'].dropna().nunique(),
        }
        
        # 🔹 EVOLUCIÓN SALARIAL
        sueldos = emp_data['Sueldo_Base_Teorico'].dropna()
        if len(sueldos) > 1:
            summary['Primer_Sueldo'] = sueldos.iloc[0]
            summary['Último_Sueldo'] = sueldos.iloc[-1]
            summary['Variación_Sueldo_Absoluta'] = sueldos.iloc[-1] - sueldos.iloc[0]
            summary['Variación_Sueldo_Porcentual'] = round(
                (sueldos.iloc[-1] / sueldos.iloc[0] - 1) * 100, 1
            ) if sueldos.iloc[0] > 0 else None
        
        # 🔹 LIQUIDACIONES
        if len(with_liquidacion) > 0:
            summary['Primer_Liquidación_Período'] = with_liquidacion.iloc[0].get('Período')
            summary['Última_Liquidación_Período'] = with_liquidacion.iloc[-1].get('Período')
            summary['Promedio_Líquido_a_Pagar'] = round(with_liquidacion['Líquido_a_Pagar'].mean(), 0)
            summary['Total_Líquido_Pagado'] = round(with_liquidacion['Líquido_a_Pagar'].sum(), 0)
        
        summary_data.append(summary)
    
    return pd.DataFrame(summary_data)

def main_complete_historical_safe():
    """
    🔹 FUNCIÓN PRINCIPAL SEGURA CON GUARDADO AUTOMÁTICO
    """
    # Configuración
    employees_url = "https://cramer.buk.cl/api/v1/chile/employees"
    liquidaciones_url = "https://cramer.buk.cl/api/v1/chile/payroll_detail/month"
    token = "Xegy8dVsa1H8SFfojJcwYtDL"

    print("=== 🚀 PROCESO DE HISTORIAL COMPLETO SEGURO ===")
    print("🔹 Características:")
    print("  ✅ Guardado automático por período en BD")
    print("  ✅ Constraint único para evitar duplicados")
    print("  ✅ Checkpoint automático para reanudar")
    print("  ✅ Manejo de Ctrl+C sin pérdida de datos")
    print("  ✅ Respaldo CSV por período")
    print()

    # Ejecutar proceso seguro
    total_processed = get_complete_historical_data_safe(employees_url, liquidaciones_url, token)
    
    if total_processed > 0:
        print(f"\n📊 Proceso completado: {total_processed:,} registros procesados")
        
        # Crear Excel final desde BD
        print("\n🔄 Creando Excel final desde base de datos...")
        df_final = create_final_excel_from_db()
        
        return df_final
    else:
        print("\n⚠️ No se procesaron registros")
        return None

# 🔹 COMANDO SQL PARA CREAR CONSTRAINT MANUALMENTE (OPCIONAL)
SQL_CREATE_CONSTRAINT = f"""
-- Ejecutar en MySQL si quieres crear la constraint manualmente:
ALTER TABLE {DB_TABLE} 
ADD CONSTRAINT uniq_emp_period 
UNIQUE KEY (ID_Empleado, Año, Mes);
"""

# 🔹 INFORMACIÓN DEL PROCESO
if __name__ == "__main__":
    print("=== 🚀 PROCESO DE HISTORIAL COMPLETO SEGURO ===")
    print("🔹 Nuevas características de seguridad:")
    print("  ✅ Guardado automático por período (no se pierde nada)")
    print("  ✅ Constraint único MySQL para evitar duplicados")
    print("  ✅ Sistema de checkpoint para reanudar donde se cortó")
    print("  ✅ Manejo de Ctrl+C sin pérdida de datos")
    print("  ✅ Respaldo CSV por período")
    print("  ✅ Excel final generado desde BD al completar")
    print()
    print("🔄 Para ejecutar:")
    print("df_historial = main_complete_historical_safe()")
    print()
    print("📋 Si se interrumpe:")
    print("  - Los datos ya están guardados en BD por períodos")
    print("  - Al ejecutar de nuevo, continúa desde donde se cortó")
    print("  - No se duplican datos gracias al constraint único")
    print()
    print("🗃️ Constraint SQL (se crea automáticamente):")
    print(SQL_CREATE_CONSTRAINT)
    
    # 🔹 EJECUTAR AUTOMÁTICAMENTE
    print("\n" + "="*50)
    print("🔄 INICIANDO PROCESO SEGURO...")
    df_historial = main_complete_historical_safe()