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

# ==== CONFIGURACIÓN BD ====
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"
DB_TABLE = "historical_settlements"

def get_db_engine():
    """Crea conexión SQLAlchemy para escritura en la BD"""
    conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(conn_str)

def save_to_db(df, table_name=DB_TABLE):
    """
    Inserta datos en BD.
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

    # Definir esquema fijo - 🔹 ACTUALIZADO con nuevas columnas
    schema = {
        "ID_Empleado": Integer(),
        "ID_Persona": Integer(),
        "RUT": String(20),
        "Nombre": String(255),
        "Género": String(20),
        "Fecha_Nacimiento": Date(),
        "Fecha_Activacion": Date(),
        "Cargo_Actual": String(255),
        "ID_Rol_Actual": Integer(),
        "Familia_Rol_Actual": String(255),
        "Sueldo_Base_Teorico": Float(),  # 🔹 NUEVO: base_wage del contrato vigente en ese período
        "Sueldo_Base_Liquidacion": Float(),  # 🔹 NUEVO: sueldo base de la liquidación específica
        "ID_Area_Actual": Integer(),
        "Tipo_Contrato_Actual": String(50),
        "Centro_Costo_Actual": String(255),
        "Horas_Semanales_Actual": Integer(),
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
            print(f"ℹ️ La tabla {table_name} no existe. Creándola con esquema fijo...")
            df.head(0).to_sql(table_name, con=engine, if_exists="replace", index=False, dtype=schema)

        # Insertar (append) en la tabla ya creada
        df.to_sql(table_name, con=engine, if_exists="append", index=False, dtype=schema)
        print(f"✅ {len(df)} registros insertados en tabla {table_name} con created_at={df['created_at'].iloc[0]}")
    except Exception as e:
        print(f"❌ Error insertando en BD: {e}")

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
    🔹 NUEVA FUNCIÓN: Extrae el sueldo base específico de la liquidación desde lines_settlement
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

def find_base_wage_for_period(employee_data, period_year, period_month):
    """
    🔹 NUEVA FUNCIÓN: Encuentra el base_wage vigente para un empleado en un período específico
    Busca en el historial de contratos (jobs) cuál estaba vigente en esa fecha
    """
    if not employee_data:
        return None
    
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
                return current_job.get('base_wage')
    
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
            return job.get('base_wage')
    
    return None

def generate_periods():
    """
    🔹 Genera períodos cada 3 meses desde enero 2019 hasta la fecha actual
    """
    periods = []
    start_date = datetime(2019, 1, 1)
    current_date = datetime.now()
    
    period_date = start_date
    while period_date <= current_date:
        periods.append({
            'month': period_date.month,
            'year': period_date.year,
            'period_label': f"{period_date.strftime('%m')}-{period_date.year}",
            'date_param': f"01-{period_date.strftime('%m')}-{period_date.year}"
        })
        period_date += relativedelta(months=3)  # 🔹 Cambio de 6 a 3 meses
    
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

def process_employee_base_data(employee_data):
    """
    🔹 MODIFICADO: Procesa los datos básicos de un empleado (datos que no cambian)
    Ya NO incluye sueldo base aquí, porque será específico por período
    """
    processed = {}
    
    # Datos básicos que no cambian
    processed['ID_Empleado'] = employee_data.get('id')
    processed['ID_Persona'] = employee_data.get('person_id')
    processed['RUT'] = employee_data.get('rut')
    processed['Nombre'] = employee_data.get('full_name')
    processed['Género'] = employee_data.get('gender')
    processed['Fecha_Nacimiento'] = employee_data.get('birthday')
    processed['Fecha_Activacion'] = employee_data.get('active_since')
    
    # Datos del trabajo actual (como referencia)
    current_job = employee_data.get('current_job', {})
    if current_job:
        # Datos del rol actual
        role = current_job.get('role', {})
        if role:
            processed['Cargo_Actual'] = role.get('name')
            processed['ID_Rol_Actual'] = role.get('id')
            
            # Datos de la familia del rol
            role_family = role.get('role_family', {})
            if role_family:
                processed['Familia_Rol_Actual'] = role_family.get('name')
        
        # 🔹 YA NO ponemos sueldo base aquí - será específico por período
        processed['ID_Area_Actual'] = current_job.get('area_id')
        processed['Tipo_Contrato_Actual'] = current_job.get('contract_type')
        processed['Centro_Costo_Actual'] = current_job.get('cost_center')
        processed['Horas_Semanales_Actual'] = current_job.get('weekly_hours')
    
    return processed

def get_historical_data_with_base_wage(employees_url, liquidaciones_url, token):
    """
    🔹 NUEVA FUNCIÓN: Obtiene historial con sueldo base teórico por período
    Requiere consultar empleados en cada período (más lento pero más preciso)
    """
    # 1. Generar períodos
    periods = generate_periods()
    all_historical_data = []
    
    print(f"Procesando {len(periods)} períodos con consultas de empleados y liquidaciones...")
    
    # 2. Para cada período, obtener empleados Y liquidaciones
    for i, period in enumerate(periods):
        print(f"Procesando período {i+1}/{len(periods)}: {period['period_label']}")
        
        # 🔹 Obtener empleados para este período específico
        employees_data = get_all_employees_data(employees_url, token)
        
        if not employees_data:
            print(f"⚠️ No se pudieron obtener empleados para {period['period_label']}")
            continue
        
        # Filtrar empleados activos
        active_employees = [emp for emp in employees_data 
                          if emp.get('status', '').lower() in ['active', 'activo']]
        
        # Excluir IDs específicos
        excluded_ids = [4804, 9386]
        filtered_employees = [emp for emp in active_employees 
                            if emp.get('id') not in excluded_ids and 
                               emp.get('person_id') not in excluded_ids]
        
        # 🔹 Obtener liquidaciones para este período
        liquidaciones_data = get_all_liquidaciones_data(liquidaciones_url, token, period['date_param'])
        
        # Crear diccionario de liquidaciones por employee_id
        liquidaciones_dict = {}
        if liquidaciones_data:
            for liq in liquidaciones_data:
                emp_id = liq.get('employee_id')
                if emp_id:
                    liquidaciones_dict[emp_id] = liq
        
        print(f"Empleados activos: {len(filtered_employees)}, Liquidaciones: {len(liquidaciones_dict)}")
        
        # 3. Para cada empleado, procesar datos para este período
        for employee in filtered_employees:
            emp_id = employee['id']
            
            # Procesar datos base del empleado
            employee_record = process_employee_base_data(employee)
            employee_record['Período'] = period['period_label']
            employee_record['Mes'] = period['month']
            employee_record['Año'] = period['year']
            
            # 🔹 NUEVO: Obtener sueldo base teórico vigente en este período
            sueldo_base_teorico = find_base_wage_for_period(employee, period['year'], period['month'])
            employee_record['Sueldo_Base_Teorico'] = sueldo_base_teorico
            
            # Calcular edad y antigüedad para este período específico
            period_date = datetime(period['year'], period['month'], 1).date()
            
            if employee_record.get('Fecha_Nacimiento'):
                employee_record['Edad'] = calculate_years_from_date(
                    employee_record['Fecha_Nacimiento'], period_date
                )
            
            if employee_record.get('Fecha_Activacion'):
                employee_record['Años_de_Servicio'] = calculate_years_from_date(
                    employee_record['Fecha_Activacion'], period_date
                )
            
            # Buscar liquidación para este empleado en este período
            liquidacion = liquidaciones_dict.get(emp_id)
            
            if liquidacion:
                # Si hay liquidación, agregar datos
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
                
                # 🔹 NUEVO: Extraer sueldo base específico de esta liquidación
                employee_record['Sueldo_Base_Liquidacion'] = extract_sueldo_base_from_liquidacion(liquidacion)
                
                # Estado del empleado en ese período (si estaba activo y tenía liquidación)
                employee_record['Estado'] = 'Activo'
            else:
                # Si no hay liquidación, dejar campos vacíos
                liquidacion_fields = [
                    'Liquidación_ID', 'Días_Trabajados', 'Días_No_Trabajados',
                    'Ingreso_Bruto', 'Ingreso_Neto', 'Ingreso_AFP', 'Ingreso_IPS',
                    'Total_Ingresos_Imponibles', 'Total_Ingresos_No_Imponibles',
                    'Total_Descuentos_Legales', 'Total_Otros_Descuentos',
                    'Líquido_a_Pagar', 'Base_Imponible', 'Cerrada', 'Sueldo_Base_Liquidacion'  # 🔹 Agregar aquí también
                ]
                for field in liquidacion_fields:
                    employee_record[field] = None
                employee_record['Tiene_Liquidación'] = False
                
                # Podría no haber estado activo en ese período
                employee_record['Estado'] = 'Sin liquidación'
            
            all_historical_data.append(employee_record)
    
    return all_historical_data

def create_historical_excel_with_base_wage(employees_url, liquidaciones_url, token, output_file='historial_empleados_con_sueldo_base.xlsx'):
    """
    🔹 NUEVA FUNCIÓN: Crea un Excel con el historial incluyendo sueldo base teórico por período
    """
    print("Iniciando obtención de datos históricos con sueldo base teórico por período...")
    
    # Obtener todos los datos históricos
    historical_data = get_historical_data_with_base_wage(employees_url, liquidaciones_url, token)
    
    if not historical_data:
        print("No se pudieron obtener datos históricos")
        return None
    
    # Convertir a DataFrame
    df = pd.DataFrame(historical_data)
    
    # Ordenar por empleado y período
    df = df.sort_values(['ID_Empleado', 'Año', 'Mes'])
    
    # Calcular rangos de edad y antigüedad
    if 'Edad' in df.columns:
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
        
        df['Rango_de_Edad'] = df['Edad'].apply(age_range)
    
    if 'Años_de_Servicio' in df.columns:
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
        
        df['Rango_de_Antigüedad'] = df['Años_de_Servicio'].apply(service_range)
    
    # 🔹 Insertar en la base de datos ANTES del Excel
    save_to_db(df)
    
    # Reordenar columnas para Excel
    column_order = [
        'Período', 'Año', 'Mes', 'ID_Empleado', 'ID_Persona', 'RUT', 'Nombre', 
        'Género', 'Edad', 'Rango_de_Edad', 'Años_de_Servicio', 'Rango_de_Antigüedad',
        'Estado', 'Cargo_Actual', 'ID_Rol_Actual', 'Familia_Rol_Actual', 
        'Sueldo_Base_Teorico', 'Sueldo_Base_Liquidacion',  # 🔹 NUEVAS COLUMNAS
        'ID_Area_Actual', 'Tipo_Contrato_Actual',
        'Centro_Costo_Actual', 'Horas_Semanales_Actual',
        'Tiene_Liquidación', 'Liquidación_ID', 'Días_Trabajados', 'Días_No_Trabajados', 
        'Ingreso_Bruto', 'Ingreso_Neto', 'Ingreso_AFP', 'Ingreso_IPS',
        'Total_Ingresos_Imponibles', 'Total_Ingresos_No_Imponibles',
        'Total_Descuentos_Legales', 'Total_Otros_Descuentos',
        'Líquido_a_Pagar', 'Base_Imponible', 'Cerrada'
    ]
    
    # Seleccionar solo columnas que existen
    available_columns = [col for col in column_order if col in df.columns]
    df_final = df[available_columns].copy()
    
    # 🔹 NUEVA HOJA: Análisis de evolución salarial
    df_salary_evolution = df_final[df_final['Sueldo_Base_Teorico'].notna()].copy()
    if len(df_salary_evolution) > 0:
        # Agregar columna de diferencia vs liquidación
        df_salary_evolution['Diferencia_Teorico_vs_Liquidacion'] = (
            df_salary_evolution['Sueldo_Base_Teorico'] - df_salary_evolution['Sueldo_Base_Liquidacion']
        )
        df_salary_evolution['Porcentaje_Liquidacion_vs_Teorico'] = (
            df_salary_evolution['Sueldo_Base_Liquidacion'] / df_salary_evolution['Sueldo_Base_Teorico'] * 100
        ).round(1)
    
    # Crear múltiples hojas en Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Hoja principal con todos los datos
        df_final.to_excel(writer, sheet_name='Historial_Completo', index=False)
        
        # 🔹 NUEVA HOJA: Evolución salarial
        if len(df_salary_evolution) > 0:
            df_salary_evolution.to_excel(writer, sheet_name='Evolucion_Salarial', index=False)
        
        # Hoja resumen por empleado
        if len(df_final) > 0:
            summary_data = []
            for emp_id in df_final['ID_Empleado'].unique():
                emp_data = df_final[df_final['ID_Empleado'] == emp_id]
                if len(emp_data) > 0:
                    latest_record = emp_data.iloc[-1]  # Último registro
                    first_record = emp_data.iloc[0]    # Primer registro
                    
                    # Encontrar primer y último período con liquidación
                    with_liquidacion = emp_data[emp_data['Tiene_Liquidación'] == True]
                    
                    summary = {
                        'ID_Empleado': emp_id,
                        'Nombre': latest_record.get('Nombre'),
                        'RUT': latest_record.get('RUT'),
                        'Cargo_Actual': latest_record.get('Cargo_Actual'),
                        'Sueldo_Base_Teorico_Actual': latest_record.get('Sueldo_Base_Teorico'),  # 🔹 ACTUALIZADO
                        'Primer_Período_Analizado': first_record.get('Período'),
                        'Último_Período_Analizado': latest_record.get('Período'),
                        'Períodos_con_Liquidación': emp_data['Tiene_Liquidación'].sum(),
                        'Total_Períodos_Analizados': len(emp_data),
                        'Porcentaje_Períodos_con_Liquidación': round(emp_data['Tiene_Liquidación'].mean() * 100, 1),
                    }
                    
                    # 🔹 NUEVO: Estadísticas de evolución salarial
                    sueldos_teoricos = emp_data['Sueldo_Base_Teorico'].dropna()
                    if len(sueldos_teoricos) > 1:
                        summary['Primer_Sueldo_Base_Teorico'] = sueldos_teoricos.iloc[0]
                        summary['Último_Sueldo_Base_Teorico'] = sueldos_teoricos.iloc[-1]
                        summary['Variación_Sueldo_Base'] = sueldos_teoricos.iloc[-1] - sueldos_teoricos.iloc[0]
                        summary['Variación_Sueldo_Base_Porcentual'] = round(
                            (sueldos_teoricos.iloc[-1] / sueldos_teoricos.iloc[0] - 1) * 100, 1
                        ) if sueldos_teoricos.iloc[0] > 0 else None
                    
                    if len(with_liquidacion) > 0:
                        first_liq = with_liquidacion.iloc[0]
                        last_liq = with_liquidacion.iloc[-1]
                        summary['Primer_Período_con_Liquidación'] = first_liq.get('Período')
                        summary['Último_Período_con_Liquidación'] = last_liq.get('Período')
                        summary['Primer_Líquido_a_Pagar'] = first_liq.get('Líquido_a_Pagar')
                        summary['Último_Líquido_a_Pagar'] = last_liq.get('Líquido_a_Pagar')
                        
                        if pd.notna(first_liq.get('Líquido_a_Pagar')) and pd.notna(last_liq.get('Líquido_a_Pagar')):
                            summary['Variación_Líquido'] = last_liq.get('Líquido_a_Pagar') - first_liq.get('Líquido_a_Pagar')
                            summary['Variación_Líquido_Porcentual'] = round(
                                (last_liq.get('Líquido_a_Pagar') / first_liq.get('Líquido_a_Pagar') - 1) * 100, 1
                            ) if first_liq.get('Líquido_a_Pagar') > 0 else None
                    
                    summary_data.append(summary)
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Resumen_por_Empleado', index=False)
        
        # Hoja de estadísticas por período
        if len(df_final) > 0:
            period_stats = df_final.groupby('Período').agg({
                'ID_Empleado': 'count',
                'Tiene_Liquidación': 'sum',
                'Sueldo_Base_Teorico': ['mean', 'median'],  # 🔹 NUEVO
                'Sueldo_Base_Liquidacion': ['mean', 'median'],  # 🔹 NUEVO
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
            
            period_stats.to_excel(writer, sheet_name='Estadísticas_por_Período', index=False)
        
        # Hoja solo con empleados que tienen liquidaciones
        df_with_liquidaciones = df_final[df_final['Tiene_Liquidación'] == True].copy()
        if len(df_with_liquidaciones) > 0:
            df_with_liquidaciones.to_excel(writer, sheet_name='Solo_con_Liquidaciones', index=False)
    
    print(f"Historial guardado en '{output_file}'")
    print(f"Total de registros: {len(df_final)}")
    print(f"Empleados únicos: {df_final['ID_Empleado'].nunique()}")
    print(f"Períodos procesados: {df_final['Período'].nunique()}")
    
    # Mostrar estadísticas de liquidaciones
    if 'Tiene_Liquidación' in df_final.columns:
        total_with_liq = df_final['Tiene_Liquidación'].sum()
        total_records = len(df_final)
        print(f"Registros con liquidación: {total_with_liq}/{total_records} ({total_with_liq/total_records*100:.1f}%)")
    
    return df_final

# ===== FUNCIÓN PRINCIPAL CON SUELDO BASE TEÓRICO =====
def main_with_base_wage():
    # Configuración
    employees_url = "https://cramer.buk.cl/api/v1/chile/employees"
    liquidaciones_url = "https://cramer.buk.cl/api/v1/chile/payroll_detail/month"
    token = "Xegy8dVsa1H8SFfojJcwYtDL"
    
    # Crear historial con sueldo base teórico
    df_historial = create_historical_excel_with_base_wage(employees_url, liquidaciones_url, token)
    
    return df_historial

# Mostrar información del proceso
if __name__ == "__main__":
    periods = generate_periods()
    print("=== PROCESO CON SUELDO BASE TEÓRICO ===")
    print(f"⚠️ ADVERTENCIA: Este proceso será MÁS LENTO")
    print(f"1. {len(periods)} consultas de empleados (una por período)")
    print(f"2. {len(periods)} consultas de liquidaciones (una por período)")
    print(f"3. Total de consultas API: {len(periods) * 2}")
    print("\n🔹 Períodos que se procesarán (cada 3 meses):")
    for period in periods:
        print(f"- {period['period_label']}")

    print(f"\nTotal de períodos: {len(periods)}")
    print("\n🔹 Nuevas columnas:")
    print("- 'Sueldo_Base_Teorico': base_wage del contrato vigente en ese período")
    print("- 'Sueldo_Base_Liquidacion': sueldo base específico de la liquidación")
    print("- Nueva hoja 'Evolucion_Salarial' con análisis comparativo")
    print("\nPara ejecutar:")
    print("df_historial = main_with_base_wage()")

    # Ejecutar
    df_historial = main_with_base_wage()