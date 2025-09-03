import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
import json
import time
import os
from dateutil.relativedelta import relativedelta
import pymysql
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.types import (
    Integer, String, Float, Date, Boolean
)
import logging
from typing import List, Dict, Optional, Tuple

# ==== CONFIGURACIÓN HULK ====
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"
DB_TABLE = "historical_settlements"

# 🔥 CONFIGURACIÓN HULK - INDESTRUCTIBLE
MAX_RETRIES = 5
RETRY_DELAY = 2  # segundos
REQUEST_TIMEOUT = 30
BATCH_SIZE = 50  # empleados por lote para guardar en BD
CHECKPOINT_FILE = "hulk_checkpoint.json"
ERROR_LOG_FILE = "hulk_errors.log"

# 🔥 CONFIGURAR LOGGING HULK
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ERROR_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HulkCheckpoint:
    """🔥 SISTEMA DE CHECKPOINT HULK - NUNCA PIERDE PROGRESO"""
    
    def __init__(self, checkpoint_file: str = CHECKPOINT_FILE):
        self.checkpoint_file = checkpoint_file
        self.data = self.load_checkpoint()
    
    def load_checkpoint(self) -> Dict:
        """Carga el checkpoint desde archivo"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"🔄 Checkpoint cargado: {data.get('last_period', 'N/A')}")
                return data
            except Exception as e:
                logger.error(f"❌ Error cargando checkpoint: {e}")
        
        return {
            'last_period_index': -1,
            'last_period': None,
            'processed_periods': [],
            'total_records': 0,
            'start_time': None,
            'errors': []
        }
    
    def save_checkpoint(self, period_index: int, period: Dict, records_count: int):
        """Guarda el progreso actual"""
        self.data.update({
            'last_period_index': period_index,
            'last_period': period['period_label'],
            'total_records': self.data.get('total_records', 0) + records_count,
            'last_update': datetime.now().isoformat(),
            'processed_periods': self.data.get('processed_periods', []) + [period['period_label']]
        })
        
        if not self.data.get('start_time'):
            self.data['start_time'] = datetime.now().isoformat()
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info(f"✅ Checkpoint guardado: {period['period_label']} ({records_count} registros)")
        except Exception as e:
            logger.error(f"❌ Error guardando checkpoint: {e}")
    
    def add_error(self, period: str, error: str):
        """Registra un error"""
        if 'errors' not in self.data:
            self.data['errors'] = []
        
        self.data['errors'].append({
            'period': period,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except:
            pass
    
    def get_resume_index(self) -> int:
        """Obtiene el índice desde donde reanudar"""
        return self.data.get('last_period_index', -1) + 1
    
    def clear_checkpoint(self):
        """Limpia el checkpoint para empezar de nuevo"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.data = self.load_checkpoint()
        logger.info("🗑️ Checkpoint limpiado")

def hulk_request(url: str, headers: Dict, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """🔥 FUNCIÓN DE REQUEST HULK - NUNCA SE RINDE"""
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"🌐 Request intento {attempt + 1}/{max_retries}: {url}")
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT
            )
            
            # Verificar status code
            if response.status_code == 429:  # Rate limit
                wait_time = RETRY_DELAY * (2 ** attempt)  # Backoff exponencial
                logger.warning(f"⏳ Rate limit detectado. Esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"✅ Request exitoso: {len(data.get('data', []))} elementos")
            return data
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏰ Timeout en intento {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"🔄 Error en intento {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
        
        except json.JSONDecodeError as e:
            logger.error(f"📄 Error decodificando JSON: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
    
    logger.error(f"💥 HULK REQUEST FAILED después de {max_retries} intentos: {url}")
    return None

def get_db_engine():
    """Crea conexión SQLAlchemy para escritura en la BD"""
    conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(conn_str)

def hulk_save_to_db(df: pd.DataFrame, table_name: str = DB_TABLE, max_retries: int = 3) -> bool:
    """🔥 GUARDADO HULK EN BD - NUNCA FALLA"""
    
    if df is None or df.empty:
        logger.warning("⚠️ No hay datos para insertar en la BD.")
        return False

    # Validar datos antes de guardar
    if not hulk_validate_dataframe(df):
        logger.error("❌ DataFrame no válido para insertar")
        return False

    df = df.copy()
    df["created_at"] = datetime.now().date()

    # Esquema fijo
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
        "Sueldo_Base_Teorico": Float(),
        "Sueldo_Base_Liquidacion": Float(),
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

    for attempt in range(max_retries):
        try:
            engine = get_db_engine()
            insp = inspect(engine)

            # Crear tabla si no existe
            if not insp.has_table(table_name):
                logger.info(f"🏗️ Creando tabla {table_name}...")
                df.head(0).to_sql(table_name, con=engine, if_exists="replace", index=False, dtype=schema)

            # Insertar en lotes para evitar timeouts
            total_inserted = 0
            for i in range(0, len(df), BATCH_SIZE):
                batch = df.iloc[i:i+BATCH_SIZE]
                batch.to_sql(table_name, con=engine, if_exists="append", index=False, dtype=schema)
                total_inserted += len(batch)
                logger.debug(f"📦 Lote insertado: {len(batch)} registros ({total_inserted}/{len(df)})")

            logger.info(f"✅ {len(df)} registros insertados en {table_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error insertando en BD (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            else:
                # Guardar datos en archivo de respaldo
                backup_file = f"hulk_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(backup_file, index=False)
                logger.error(f"💾 Datos guardados en respaldo: {backup_file}")
                return False

    return False

def hulk_validate_dataframe(df: pd.DataFrame) -> bool:
    """🔥 VALIDACIÓN HULK DE DATAFRAME"""
    
    if df is None or df.empty:
        return False
    
    required_columns = ['ID_Empleado', 'Período', 'Año', 'Mes']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"❌ Columnas faltantes: {missing_columns}")
        return False
    
    # Verificar que no haya IDs nulos
    if df['ID_Empleado'].isnull().any():
        logger.error("❌ IDs de empleado nulos encontrados")
        return False
    
    return True

def hulk_get_all_employees_data(base_url: str, token: str) -> List[Dict]:
    """🔥 OBTENER EMPLEADOS HULK - NUNCA FALLA"""
    
    all_data = []
    page = 1
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    logger.info(f"🚀 Iniciando descarga de empleados...")
    
    while True:
        url = f"{base_url}?page_size=100&page={page}"
        headers = {"auth_token": token}
        
        data = hulk_request(url, headers)
        
        if data is None:
            consecutive_failures += 1
            logger.error(f"💥 Fallo en página {page} (fallos consecutivos: {consecutive_failures})")
            
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"💀 Demasiados fallos consecutivos. Abortando descarga de empleados.")
                break
            
            page += 1
            continue
        
        consecutive_failures = 0  # Reset contador
        current_data = data.get('data', [])
        
        if not current_data or len(current_data) == 0:
            logger.info(f"✅ Descarga de empleados completada. Total páginas: {page-1}")
            break
            
        all_data.extend(current_data)
        logger.info(f"📄 Página {page}: {len(current_data)} empleados ({len(all_data)} total)")
        
        if len(current_data) < 100:
            break
            
        page += 1
        time.sleep(0.1)  # Rate limiting preventivo
    
    logger.info(f"👥 Total empleados obtenidos: {len(all_data)}")
    return all_data

def hulk_get_all_liquidaciones_data(base_url: str, token: str, date_param: str) -> List[Dict]:
    """🔥 OBTENER LIQUIDACIONES HULK - NUNCA FALLA"""
    
    all_data = []
    page = 1
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    logger.info(f"💰 Iniciando descarga de liquidaciones para {date_param}...")
    
    while True:
        url = f"{base_url}?date={date_param}&page_size=100&page={page}"
        headers = {"auth_token": token}
        
        data = hulk_request(url, headers)
        
        if data is None:
            consecutive_failures += 1
            logger.error(f"💥 Fallo en liquidaciones página {page} (fallos consecutivos: {consecutive_failures})")
            
            if consecutive_failures >= max_consecutive_failures:
                logger.error(f"💀 Demasiados fallos consecutivos. Abortando descarga de liquidaciones.")
                break
            
            page += 1
            continue
        
        consecutive_failures = 0
        current_data = data.get('data', [])
        
        if not current_data or len(current_data) == 0:
            logger.info(f"✅ Descarga de liquidaciones completada. Total páginas: {page-1}")
            break
            
        all_data.extend(current_data)
        logger.debug(f"📄 Liquidaciones página {page}: {len(current_data)} ({len(all_data)} total)")
        
        if len(current_data) < 100:
            break
            
        page += 1
        time.sleep(0.1)  # Rate limiting preventivo
    
    logger.info(f"💰 Total liquidaciones obtenidas: {len(all_data)}")
    return all_data

def extract_sueldo_base_from_liquidacion(liquidacion_data):
    """Extrae el sueldo base específico de la liquidación desde lines_settlement"""
    if not liquidacion_data or 'lines_settlement' not in liquidacion_data:
        return None

    lines = liquidacion_data.get('lines_settlement', [])

    for line in lines:
        if (line.get('type') == 'haber' and
            line.get('code') == 'wage' and
            line.get('name') == 'Sueldo Base'):
            return line.get('amount')

    return None

def find_base_wage_for_period(employee_data, period_year, period_month):
    """Encuentra el base_wage vigente para un empleado en un período específico"""
    if not employee_data:
        return None
    
    period_date = datetime(period_year, period_month, 1).date()
    
    # Revisar current_job
    current_job = employee_data.get('current_job', {})
    if current_job:
        start_date_str = current_job.get('start_date')
        end_date_str = current_job.get('end_date')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = None
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                if start_date <= period_date and (end_date is None or period_date <= end_date):
                    return current_job.get('base_wage')
            except ValueError:
                pass
    
    # Buscar en jobs históricos
    jobs = employee_data.get('jobs', [])
    for job in jobs:
        start_date_str = job.get('start_date')
        end_date_str = job.get('end_date')
        
        if not start_date_str:
            continue
            
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = None
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if start_date <= period_date and (end_date is None or period_date <= end_date):
                return job.get('base_wage')
        except ValueError:
            continue
    
    return None

def generate_periods():
    """Genera períodos cada 3 meses desde enero 2019 hasta la fecha actual"""
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
        period_date += relativedelta(months=3)
    
    return periods

def calculate_years_from_date(start_date, reference_date):
    """Calcula años desde una fecha hasta una fecha de referencia"""
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
    """Procesa los datos básicos de un empleado"""
    processed = {}
    
    processed['ID_Empleado'] = employee_data.get('id')
    processed['ID_Persona'] = employee_data.get('person_id')
    processed['RUT'] = employee_data.get('rut')
    processed['Nombre'] = employee_data.get('full_name')
    processed['Género'] = employee_data.get('gender')
    processed['Fecha_Nacimiento'] = employee_data.get('birthday')
    processed['Fecha_Activacion'] = employee_data.get('active_since')
    
    current_job = employee_data.get('current_job', {})
    if current_job:
        role = current_job.get('role', {})
        if role:
            processed['Cargo_Actual'] = role.get('name')
            processed['ID_Rol_Actual'] = role.get('id')
            
            role_family = role.get('role_family', {})
            if role_family:
                processed['Familia_Rol_Actual'] = role_family.get('name')
        
        processed['ID_Area_Actual'] = current_job.get('area_id')
        processed['Tipo_Contrato_Actual'] = current_job.get('contract_type')
        processed['Centro_Costo_Actual'] = current_job.get('cost_center')
        processed['Horas_Semanales_Actual'] = current_job.get('weekly_hours')
    
    return processed

def hulk_get_historical_data_with_base_wage(employees_url: str, liquidaciones_url: str, token: str, resume: bool = True) -> List[Dict]:
    """🔥 FUNCIÓN HULK PRINCIPAL - INDESTRUCTIBLE CON CHECKPOINTS"""
    
    # Inicializar checkpoint
    checkpoint = HulkCheckpoint()
    
    if not resume:
        checkpoint.clear_checkpoint()
        logger.info("🗑️ Iniciando proceso desde cero")
    
    periods = generate_periods()
    all_historical_data = []
    
    # Determinar desde dónde reanudar
    start_index = checkpoint.get_resume_index() if resume else 0
    
    if start_index > 0:
        logger.info(f"🔄 Reanudando desde período {start_index + 1}/{len(periods)}")
    else:
        logger.info(f"🚀 Iniciando proceso HULK con {len(periods)} períodos")
    
    # Procesar períodos
    for i in range(start_index, len(periods)):
        period = periods[i]
        period_start_time = time.time()
        
        logger.info(f"🔥 HULK PROCESANDO [{i+1}/{len(periods)}]: {period['period_label']}")
        
        try:
            # Obtener empleados
            employees_data = hulk_get_all_employees_data(employees_url, token)
            
            if not employees_data:
                error_msg = f"No se pudieron obtener empleados para {period['period_label']}"
                logger.error(f"❌ {error_msg}")
                checkpoint.add_error(period['period_label'], error_msg)
                continue
            
            # Filtrar empleados
            active_employees = [emp for emp in employees_data 
                              if emp.get('status', '').lower() in ['active', 'activo']]
            
            excluded_ids = [4804, 9386]
            filtered_employees = [emp for emp in active_employees 
                                if emp.get('id') not in excluded_ids and 
                                   emp.get('person_id') not in excluded_ids]
            
            # Obtener liquidaciones
            liquidaciones_data = hulk_get_all_liquidaciones_data(liquidaciones_url, token, period['date_param'])
            
            # Crear diccionario de liquidaciones
            liquidaciones_dict = {}
            if liquidaciones_data:
                for liq in liquidaciones_data:
                    emp_id = liq.get('employee_id')
                    if emp_id:
                        liquidaciones_dict[emp_id] = liq
            
            logger.info(f"👥 Empleados: {len(filtered_employees)}, 💰 Liquidaciones: {len(liquidaciones_dict)}")
            
            # Procesar empleados para este período
            period_data = []
            
            for employee in filtered_employees:
                try:
                    emp_id = employee['id']
                    
                    # Procesar datos base
                    employee_record = process_employee_base_data(employee)
                    employee_record['Período'] = period['period_label']
                    employee_record['Mes'] = period['month']
                    employee_record['Año'] = period['year']
                    
                    # Sueldo base teórico
                    sueldo_base_teorico = find_base_wage_for_period(employee, period['year'], period['month'])
                    employee_record['Sueldo_Base_Teorico'] = sueldo_base_teorico
                    
                    # Calcular edad y antigüedad
                    period_date = datetime(period['year'], period['month'], 1).date()
                    
                    if employee_record.get('Fecha_Nacimiento'):
                        employee_record['Edad'] = calculate_years_from_date(
                            employee_record['Fecha_Nacimiento'], period_date
                        )
                    
                    if employee_record.get('Fecha_Activacion'):
                        employee_record['Años_de_Servicio'] = calculate_years_from_date(
                            employee_record['Fecha_Activacion'], period_date
                        )
                    
                    # Buscar liquidación
                    liquidacion = liquidaciones_dict.get(emp_id)
                    
                    if liquidacion:
                        # Con liquidación
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
                        employee_record['Sueldo_Base_Liquidacion'] = extract_sueldo_base_from_liquidacion(liquidacion)
                        employee_record['Estado'] = 'Activo'
                    else:
                        # Sin liquidación
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
                        employee_record['Estado'] = 'Sin liquidación'
                    
                    period_data.append(employee_record)
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando empleado {emp_id}: {e}")
                    continue
            
            # Convertir a DataFrame y agregar rangos
            if period_data:
                df_period = pd.DataFrame(period_data)
                
                # Calcular rangos
                if 'Edad' in df_period.columns:
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
                    
                    df_period['Rango_de_Edad'] = df_period['Edad'].apply(age_range)
                
                if 'Años_de_Servicio' in df_period.columns:
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
                    
                    df_period['Rango_de_Antigüedad'] = df_period['Años_de_Servicio'].apply(service_range)
                
                # 🔥 GUARDADO HULK INCREMENTAL
                if hulk_save_to_db(df_period):
                    all_historical_data.extend(period_data)
                    
                    # Guardar checkpoint
                    checkpoint.save_checkpoint(i, period, len(period_data))
                    
                    period_time = time.time() - period_start_time
                    logger.info(f"✅ HULK COMPLETÓ {period['period_label']}: {len(period_data)} registros en {period_time:.1f}s")
                else:
                    error_msg = f"Error guardando datos en BD para {period['period_label']}"
                    logger.error(f"❌ {error_msg}")
                    checkpoint.add_error(period['period_label'], error_msg)
            else:
                logger.warning(f"⚠️ No hay datos para procesar en {period['period_label']}")
        
        except Exception as e:
            error_msg = f"Error crítico procesando {period['period_label']}: {e}"
            logger.error(f"💥 {error_msg}")
            checkpoint.add_error(period['period_label'], error_msg)
            continue
    
    logger.info(f"🎉 HULK TERMINÓ! Total registros procesados: {len(all_historical_data)}")
    return all_historical_data

def hulk_create_excel_from_db(output_file: str = 'hulk_historial_completo.xlsx'):
    """🔥 CREAR EXCEL HULK DESDE LA BD"""
    
    logger.info("📊 Creando Excel HULK desde la base de datos...")
    
    try:
        engine = get_db_engine()
        
        # Leer todos los datos de la BD
        query = f"SELECT * FROM {DB_TABLE} ORDER BY ID_Empleado, Año, Mes"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            logger.error("❌ No hay datos en la base de datos")
            return None
        
        logger.info(f"📊 Datos cargados: {len(df)} registros, {df['ID_Empleado'].nunique()} empleados únicos")
        
        # Crear Excel con múltiples hojas
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Hoja principal
            df.to_excel(writer, sheet_name='Historial_Completo', index=False)
            
            # Hoja con liquidaciones
            df_with_liq = df[df['Tiene_Liquidación'] == True].copy()
            if len(df_with_liq) > 0:
                df_with_liq.to_excel(writer, sheet_name='Solo_con_Liquidaciones', index=False)
            
            # Estadísticas por período
            if len(df) > 0:
                period_stats = df.groupby('Período').agg({
                    'ID_Empleado': 'count',
                    'Tiene_Liquidación': 'sum',
                    'Sueldo_Base_Teorico': ['mean', 'median'],
                    'Sueldo_Base_Liquidacion': ['mean', 'median'],
                    'Líquido_a_Pagar': ['count', 'mean', 'median', 'sum'],
                    'Ingreso_Bruto': ['mean', 'median'],
                    'Días_Trabajados': 'mean'
                }).round(0)
                
                period_stats.columns = ['_'.join(col).strip() for col in period_stats.columns]
                period_stats = period_stats.reset_index()
                
                period_stats['Porcentaje_con_Liquidación'] = round(
                    (period_stats['Tiene_Liquidación_sum'] / period_stats['ID_Empleado_count']) * 100, 1
                )
                
                period_stats.to_excel(writer, sheet_name='Estadísticas_por_Período', index=False)
        
        logger.info(f"✅ Excel HULK creado: {output_file}")
        return df
        
    except Exception as e:
        logger.error(f"❌ Error creando Excel: {e}")
        return None

# 🔥 FUNCIÓN PRINCIPAL HULK
def hulk_main(resume: bool = True, create_excel: bool = True):
    """🔥 FUNCIÓN PRINCIPAL HULK - INDESTRUCTIBLE"""
    
    logger.info("🔥🔥🔥 INICIANDO PROCESO HULK 🔥🔥🔥")
    
    # Configuración
    employees_url = "https://cramer.buk.cl/api/v1/chile/employees"
    liquidaciones_url = "https://cramer.buk.cl/api/v1/chile/payroll_detail/month"
    token = "Xegy8dVsa1H8SFfojJcwYtDL"
    
    start_time = time.time()
    
    try:
        # Procesar datos históricos
        historical_data = hulk_get_historical_data_with_base_wage(
            employees_url, liquidaciones_url, token, resume=resume
        )
        
        # Crear Excel si se solicita
        df_final = None
        if create_excel:
            df_final = hulk_create_excel_from_db()
        
        total_time = time.time() - start_time
        logger.info(f"🎉 HULK COMPLETADO en {total_time/60:.1f} minutos")
        
        return df_final
        
    except Exception as e:
        logger.error(f"💥 ERROR CRÍTICO HULK: {e}")
        return None

# 🔥 FUNCIONES DE UTILIDAD HULK
def hulk_status():
    """🔥 VER ESTADO DEL PROCESO HULK"""
    checkpoint = HulkCheckpoint()
    
    print("🔥 ESTADO HULK:")
    print(f"📊 Último período procesado: {checkpoint.data.get('last_period', 'N/A')}")
    print(f"📈 Total registros: {checkpoint.data.get('total_records', 0)}")
    print(f"⏰ Inicio: {checkpoint.data.get('start_time', 'N/A')}")
    print(f"🔄 Última actualización: {checkpoint.data.get('last_update', 'N/A')}")
    print(f"❌ Errores: {len(checkpoint.data.get('errors', []))}")
    
    if checkpoint.data.get('errors'):
        print("\n❌ ERRORES:")
        for error in checkpoint.data['errors'][-5:]:  # Últimos 5 errores
            print(f"  - {error['period']}: {error['error']}")

def hulk_reset():
    """🔥 RESETEAR PROCESO HULK"""
    checkpoint = HulkCheckpoint()
    checkpoint.clear_checkpoint()
    
    # Limpiar logs
    if os.path.exists(ERROR_LOG_FILE):
        os.remove(ERROR_LOG_FILE)
    
    print("🗑️ HULK RESETEADO - Listo para empezar de nuevo")

# 🔥 EJECUCIÓN
if __name__ == "__main__":
    print("🔥🔥🔥 CÓDIGO HULK CARGADO 🔥🔥🔥")
    print("\nComandos disponibles:")
    print("- hulk_main()           # Ejecutar proceso completo")
    print("- hulk_main(resume=False) # Empezar desde cero")
    print("- hulk_status()         # Ver estado actual")
    print("- hulk_reset()          # Resetear todo")
    print("- hulk_create_excel_from_db() # Solo crear Excel desde BD")
    
    # Para ejecutar automáticamente:
    df_historial = hulk_main()