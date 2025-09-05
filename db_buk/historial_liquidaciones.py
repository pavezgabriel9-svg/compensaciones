#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HULK - Extractor de Datos Históricos de Empleados con Historial de Cargos
Versión Optimizada con doble funcionalidad:
1. Extrae liquidaciones históricas (tabla original)
2. Extrae historial de cargos por empleado (nueva funcionalidad)

Autor: Optimizado para eficiencia y conservación de recursos
Fecha: 2025
"""

import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, inspect
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# ==== CONFIGURACIÓN HULK ====
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# TABLAS DE DESTINO
DB_TABLE_SETTLEMENTS = "total_liquidaciones"  # Tabla original de liquidaciones
DB_TABLE_JOB_HISTORY = "historial_cargos_empleados"  # Nueva tabla de historial de cargos

# API CONFIGURATION
BUK_BASE = "https://cramer.buk.cl/api/v1/chile"
API_EMPLOYEES = f"{BUK_BASE}/employees"
API_PAYROLL_MONTH = f"{BUK_BASE}/payroll_detail/month"
API_TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

# CONFIGURACIÓN OPTIMIZADA
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
BATCH_SIZE = 500
MAX_WORKERS = 3
DELAY_BETWEEN_REQUESTS = 1.0

# ==== CONFIGURACIÓN DE LOGGING ====
logging.basicConfig(
    level=logging.DEBUG,  # 👈 cambia INFO por DEBUG
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_db_engine():
    """Crear conexión a la base de datos"""
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(connection_string, pool_recycle=3600, pool_pre_ping=True)

class HulkProgressTracker:
    """Clase para trackear progreso y hacer checkpoints"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.processed_periods = 0
        self.total_records = 0
        self.errors = []
        
    def save_checkpoint(self, period_index, period, records_count, error=None):
        """Guardar checkpoint del progreso"""
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                settlements_count = conn.execute(text(f"SELECT COUNT(*) FROM {DB_TABLE_SETTLEMENTS}")).scalar()
                job_history_count = conn.execute(text(f"SELECT COUNT(*) FROM {DB_TABLE_JOB_HISTORY}")).scalar()
                
                checkpoint_data = {
                    'timestamp': datetime.now().isoformat(),
                    'period_index': period_index,
                    'period': period,
                    'records_count': records_count,
                    'total_settlements': settlements_count,
                    'total_job_history': job_history_count,
                    'error': str(error) if error else None
                }
                
                logger.info(f"📊 Checkpoint - Período {period}: {records_count} registros | "
                          f"Total liquidaciones: {settlements_count} | Total historial cargos: {job_history_count}")
                
                if error:
                    self.errors.append(checkpoint_data)
                    
        except Exception as e:
            logger.error(f"❌ Error guardando checkpoint: {e}")

def hulk_make_api_request(url: str, headers: Dict, params: Dict = None, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """Realizar petición a la API con reintentos optimizados"""
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"🌐 Request → URL: {url} | Params: {params} | Headers: {headers}")
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                wait_time = min(2 ** attempt, 10)
                logger.warning(f"⚠️ Rate limit alcanzado. Esperando {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Error API {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout en intento {attempt + 1}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error de conexión: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(1)
            
    return None

def hulk_save_to_db(df: pd.DataFrame, table_name: str, max_retries: int = 2) -> bool:
    if df.empty:
        logger.warning("⚠️ DataFrame vacío, no se guardará nada")
        return True

    engine = get_db_engine()
    insp = inspect(engine)
    table_exists = insp.has_table(table_name)

    for attempt in range(max_retries):
        try:
            if not table_exists:
                df.head(0).to_sql(table_name, engine, if_exists='replace', index=False)
                table_exists = True

            df.to_sql(
                table_name,
                engine,
                if_exists='append',
                index=False,
                chunksize=BATCH_SIZE,
                method='multi'
            )
            logger.info(f"✅ Guardados {len(df)} registros en tabla '{table_name}'")
            return True

        except Exception as e:
            logger.error(f"❌ Error guardando en BD (intento {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    return False

# ==== NUEVO: funciones para payroll_detail/month ====
def period_to_buk_date(period: str) -> str:
    """Convierte YYYY-MM a 01-MM-YYYY"""
    year, month = period.split("-")
    return f"01-{month}-{year}"

def get_payroll_detail_month(period: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Obtiene el detalle de liquidaciones para un período (YYYY-MM).
    """
    params = {"date": f"01-{period.split('-')[1]}-{period.split('-')[0]}"}
    data = hulk_make_api_request(API_PAYROLL_MONTH, headers, params)

    # 🔍 Debug mejorado
    logger.debug(f"🔎 Tipo de respuesta Payroll → {type(data)}")

    if isinstance(data, dict):
        logger.debug(f"🔎 Claves en respuesta Payroll → {list(data.keys())}")

        if "data" in data and isinstance(data["data"], list):
            logger.debug(f"🔎 Total items en data → {len(data['data'])}")
            if len(data["data"]) > 0:
                logger.debug(f"🔎 Ejemplo item Payroll → {str(data['data'][0])[:500]}")
            return data["data"]
        else:
            logger.warning("⚠️ La respuesta Payroll no contiene 'data' o no es lista")
            return []
    else:
        logger.debug(f"🔎 Respuesta Payroll cruda (no dict) → {str(data)[:500]}")
        return []


def parse_payroll_item(item: Dict) -> Tuple[Optional[int], Optional[str], float, Optional[str], float]:
    """Normaliza los campos de cada liquidación"""
    employee_id = (
        item.get("employee_id")
        or (item.get("employee") or {}).get("id")
        or (item.get("employee") or {}).get("employee_id")
    )
    settlement_id = item.get("id") or item.get("payroll_id") or item.get("settlement_id")

    liquido = (
        item.get("liquid_reach")
        or item.get("liquid")
        or item.get("net_pay")
        or 0.0
    ) or 0.0

    total_amount = (
        item.get("total_amount")
        or item.get("total")
        or item.get("gross_pay")
        or liquido
        or 0.0
    ) or 0.0

    status = item.get("status") or item.get("payroll_status")

    return employee_id, settlement_id, float(total_amount), status, float(liquido)

# ==== Funciones existentes para jobs/empleados ====
def extract_job_history(employee_data: Dict) -> List[Dict]:
    historial_cargos = []
    person_id = employee_data.get('person_id')
    employee_id = employee_data.get('id')
    full_name = employee_data.get('full_name')
    rut = employee_data.get('rut')
    
    for job in employee_data.get('jobs', []):
        role = job.get('role', {})
        boss = job.get('boss', {})
        
        cargo_record = {
            "ID_Empleado": employee_id,
            "ID_Persona": person_id,
            "RUT": rut,
            "Nombre_Completo": full_name,
            "Job_ID": job.get('id'),
            "Cargo": role.get('name'),
            "Codigo_Cargo": role.get('code'),
            "Sueldo_Base": job.get('base_wage'),
            "Tipo_Contrato": job.get('contract_type'),
            "Fecha_Inicio": job.get('start_date'),
            "Fecha_Fin": job.get('end_date'),
            "Area_ID": job.get('area_id'),
            "Centro_Costo": job.get('cost_center'),
            "Horas_Semanales": job.get('weekly_hours'),
            "Jefe_ID": boss.get('id') if boss else None,
            "Jefe_RUT": boss.get('rut') if boss else None,
            "Moneda": job.get('currency_code'),
            "Fecha_Suscripcion_Contrato": job.get('contract_subscription_date'),
            "Tipo_Jornada": job.get('working_schedule_type'),
            "Periodicidad": job.get('periodicity'),
            "Frecuencia": job.get('frequency'),
            "Fecha_Extraccion": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        historial_cargos.append(cargo_record)
    
    return historial_cargos

def process_employee_base_data(employee_data: Dict) -> Tuple[Dict, List[Dict]]:
    current_job = employee_data.get('current_job', {})
    role = current_job.get('role', {})
    
    base_data = {
        "ID_Empleado": employee_data.get('id'),
        "ID_Persona": employee_data.get('person_id'),
        "RUT": employee_data.get('rut'),
        "Nombre": employee_data.get('first_name'),
        "Apellido": employee_data.get('surname'),
        "Segundo_Apellido": employee_data.get('second_surname'),
        "Nombre_Completo": employee_data.get('full_name'),
        "Email": employee_data.get('email'),
        "Telefono": employee_data.get('phone'),
        "Cargo_Actual": role.get('name'),
        "Sueldo_Base_Actual": current_job.get('base_wage'),
        "Tipo_Contrato": current_job.get('contract_type'),
        "Area_ID": current_job.get('area_id'),
        "Centro_Costo": current_job.get('cost_center'),
        "Estado": employee_data.get('status'),
        "Fecha_Ingreso": employee_data.get('active_since'),
        "Fecha_Extraccion": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    job_history = extract_job_history(employee_data)
    
    return base_data, job_history

# ==== Principal ====
def hulk_get_historical_data_with_job_history(start_year: int = 2023, end_year: int = 2025) -> bool:
    logger.info("🚀 HULK iniciando extracción de datos históricos + historial de cargos")
    
    tracker = HulkProgressTracker()
    headers = {"Auth-Token": API_TOKEN}
    
    # Generar períodos YYYY-MM
    periods = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            periods.append(f"{year}-{month:02d}")
    
    logger.info(f"📅 Procesando {len(periods)} períodos desde {start_year} hasta {end_year}")
    
    all_job_history = []
    
    for period_index, period in enumerate(periods):
        logger.info(f"🔄 Procesando período {period} ({period_index + 1}/{len(periods)})")
        
        try:
            # 1. Obtener liquidaciones del mes
            settlements_items = get_payroll_detail_month(period, headers)

            if not settlements_items:
                logger.warning(f"⚠️ No se pudieron obtener liquidaciones para {period}")
                tracker.save_checkpoint(period_index, period, 0, "No data from payroll_detail/month")
                continue

            settlements_records = []
            employee_ids_processed = set()

            for item in settlements_items:
                employee_id, settlement_id, total_amount, status, liquido = parse_payroll_item(item)
                if not employee_id:
                    continue

                if employee_id not in employee_ids_processed:
                    employee_url = f"{API_EMPLOYEES}/{employee_id}"
                    employee_data = hulk_make_api_request(employee_url, headers)

                    if employee_data and 'data' in employee_data:
                        data_obj = employee_data['data']

                        # Si data es lista, saco el primer elemento
                        if isinstance(data_obj, list) and len(data_obj) > 0:
                            employee_info = data_obj[0]
                        # Si data es dict, lo uso directo
                        elif isinstance(data_obj, dict):
                            employee_info = data_obj
                        else:
                            logger.warning(f"⚠️ Respuesta inesperada al obtener empleado {employee_id}: {type(data_obj)}")
                            continue  

                        base_data, job_history = process_employee_base_data(employee_info)
                        all_job_history.extend(job_history)

                        settlement_record = base_data.copy()
                        settlement_record.update({
                            "Período": period,
                            "Año": int(period.split('-')[0]),
                            "Mes": int(period.split('-')[1]),
                            "Settlement_ID": settlement_id,
                            "Monto_Liquidacion": total_amount,
                            "Estado_Liquidacion": status,
                            "Liquido_a_Pagar": liquido
                        })

                        settlements_records.append(settlement_record)
                        employee_ids_processed.add(employee_id)

                    time.sleep(DELAY_BETWEEN_REQUESTS)

            # 2. Guardar liquidaciones en BD
            if settlements_records:
                df_settlements = pd.DataFrame(settlements_records)
                success = hulk_save_to_db(df_settlements, DB_TABLE_SETTLEMENTS)
                
                if not success:
                    logger.error(f"❌ Error guardando liquidaciones del período {period}")
                    tracker.save_checkpoint(period_index, period, len(settlements_records), "DB save error")
                    continue
            
            tracker.save_checkpoint(period_index, period, len(settlements_records))
            tracker.processed_periods += 1
            tracker.total_records += len(settlements_records)
            
        except Exception as e:
            logger.exception(f"❌ Error procesando período {period}")
            tracker.save_checkpoint(period_index, period, 0, str(e))
            continue
    
    # 3. Guardar historial de cargos completo
    logger.info(f"💾 Guardando historial completo de cargos: {len(all_job_history)} registros")
    
    if all_job_history:
        df_job_history = pd.DataFrame(all_job_history)
        df_job_history = df_job_history.drop_duplicates(subset=['Job_ID'], keep='first')
        
        success = hulk_save_to_db(df_job_history, DB_TABLE_JOB_HISTORY)
        
        if success:
            logger.info(f"✅ Historial de cargos guardado exitosamente: {len(df_job_history)} registros únicos")
        else:
            logger.error("❌ Error guardando historial de cargos")
    
    elapsed_time = datetime.now() - tracker.start_time
    logger.info(f"""
    🎯 HULK COMPLETADO
    ⏱️ Tiempo total: {elapsed_time}
    📊 Períodos procesados: {tracker.processed_periods}/{len(periods)}
    📝 Total liquidaciones: {tracker.total_records}
    🏢 Total historial cargos: {len(all_job_history)}
    ❌ Errores: {len(tracker.errors)}
    """)
    
    return len(tracker.errors) == 0

# def hulk_create_excel_from_db(output_file: str = 'hulk_historial_completo.xlsx'):
#     """Crear Excel con datos de ambas tablas"""
#     try:
#         engine = get_db_engine()
        
#         with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
#             query_settlements = f"SELECT * FROM {DB_TABLE_SETTLEMENTS} ORDER BY ID_Empleado, Año, Mes"
#             df_settlements = pd.read_sql(query_settlements, engine)
#             df_settlements.to_excel(writer, sheet_name='Liquidaciones_Historicas', index=False)
            
#             query_job_history = f"SELECT * FROM {DB_TABLE_JOB_HISTORY} ORDER BY ID_Empleado, Fecha_Inicio"
#             df_job_history = pd.read_sql(query_job_history, engine)
#             df_job_history.to_excel(writer, sheet_name='Historial_Cargos', index=False)
            
#             logger.info(f"✅ Excel creado: {output_file}")
#             logger.info(f"📊 Liquidaciones: {len(df_settlements)} registros")
#             logger.info(f"🏢 Historial cargos: {len(df_job_history)} registros")
            
#     except Exception as e:
#         logger.error(f"❌ Error creando Excel: {e}")

if __name__ == "__main__":
    print("🚀 HULK - Extractor de Datos Históricos + Historial de Cargos")
    print("=" * 60)
    
    success = hulk_get_historical_data_with_job_history(start_year=2023, end_year=2025)
    
    if success:
        print("\n✅ Extracción completada exitosamente")
        #hulk_create_excel_from_db()
        print("📊 Excel generado con ambas tablas")
    else:
        print("\n❌ Extracción completada con errores. Revisar logs.")
    