import requests
import time
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.types import Integer, String, Float, Date, Boolean, Text
import logging
import sys
import json
import traceback
import sys
import io


# ========== CONFIGURACIÓN LOGGING ==========
# Crear un logger personalizado
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configurar el formato del log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Manejador para la consola
handler_console = logging.StreamHandler(sys.stdout)
handler_console.setLevel(logging.INFO)
handler_console.setFormatter(formatter)
logger.addHandler(handler_console)

# Manejador para el archivo
handler_file = logging.FileHandler('etl_log.log')
handler_file.setLevel(logging.INFO)
handler_file.setFormatter(formatter)
logger.addHandler(handler_file)

# ========== CONFIGURACIÓN BD ==========
# Configuración BD - mac
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "conexion_buk"

# Configuración BD - windows
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

# Nombre tablas
TABLE_PAYROLLS = "historical_settlements"
TABLE_ITEMS = "historical_settlement_items"

# Tamaño de pagina para la API
PAGE_SIZE = 100

def get_db_engine():
    conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(conn_str, pool_recycle=3600)

# ------------------ Utils API ------------------
def request_with_retry(session, url, headers, max_retries=5, backoff_base=1.5, timeout=30):
    """
    Realiza GET con reintentos exponenciales
    Devuelve response.json() o lanza excepción si falla despues de retries.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            resp = session.get(url, headers=headers, timeout=timeout)
            # Si 5xx -> retry
            if 500 <= resp.status_code < 600:
                raise requests.exceptions.HTTPError(f"Server error {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError) as e:
            attempt += 1
            wait = backoff_base ** attempt
            logger.warning(f"  Request error (attempt {attempt}/{max_retries}) for URL: {url}\n     {e}\n     Waiting {wait:.1f}s before retry")
            time.sleep(wait)
        except Exception as e:
            # errores inesperados: no reintentar muchas veces
            attempt += 1
            wait = backoff_base ** attempt
            logger.warning(f"  Unexpected error (attempt {attempt}/{max_retries}): {e}\n     Waiting {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to GET {url} after {max_retries} attempts")

def get_all_liquidaciones_data(base_url, token, date_param):
    """
    Pagina y obtiene todas las liquidaciones para date_param (formato dd-mm-YYYY).
    Usa request_with_retry para tolerar errores temporales.
    Devuelve lista de liquidaciones (list of dicts).
    """
    session = requests.Session()
    headers = {"auth_token": token}
    page = 1
    all_data = []

    while True:
        url = f"{base_url}?date={date_param}&page_size={PAGE_SIZE}&page={page}"
        try:
            data = request_with_retry(session, url, headers)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(" Error de autenticación! Token inválido o expirado.")
                raise # Propagar el error para detener la ejecución
            else:
                logger.error(f"   Error HTTP inesperado en la página {page} para {date_param}: {e}")
                raise
        except Exception as e:
            logger.error(f"   Error obteniendo página {page} para {date_param}: {e}")
            raise

        page_data = data.get("data", [])
        if not page_data:
            break

        all_data.extend(page_data)

        # paginación simple: si cantidad < PAGE_SIZE -> última página
        if len(page_data) < PAGE_SIZE:
            break

        page += 1
        # leve pausa entre páginas
        time.sleep(0.2)

    return all_data

# ------------------ Transformaciones ------------------
def flatten_liquidation(liq):
    """
    Genera un dict plano (fila) a partir de una liquidación.
    Nombres de columnas sin tildes para evitar problemas.
    """
    # Convertir fecha periodo: usar primer día del mes
    year = liq.get("year")
    month = liq.get("month")
    
    if year and month:
        try:
            year_int = int(year)
            month_int = int(month)
            pay_period = date(year_int, month_int, 1)
            period_label = f"{month_int:02d}-{year_int}"
        except Exception as e:
            print(f"ERROR convirtiendo fecha: year={year}, month={month}, error={e}")
            pay_period = None
            period_label = None
            year_int = None
            month_int = None
    else:
        pay_period = None
        period_label = None
        year_int = None
        month_int = None

    liquidacion_id = liq.get("liquidacion_id")
    if not liquidacion_id:
        print(f"WARNING: liquidacion_id es None o vacío para registro: {liq}")

    flattened = {
        "Liquidacion_ID": liquidacion_id,
        "ID_Persona": liq.get("person_id"),
        "ID_Empleado": liq.get("employee_id"),
        "RUT": liq.get("rut"),
        "Período": period_label,
        "Año": year_int,
        "Mes": month_int,
        "Pay_Period": pay_period,
        "Días_Trabajados": liq.get("worked_days"),
        "Días_No_Trabajados": liq.get("noworked_days"),
        "Ingreso_Bruto": liq.get("income_gross"),
        "Ingreso_Neto": liq.get("income_net"),
        "Ingreso_AFP": liq.get("income_afp"),
        "Ingreso_IPS": liq.get("income_ips"),
        "Total_Ingresos_Imponibles": liq.get("total_income_taxable"),
        "Total_Ingresos_No_Imponibles": liq.get("total_income_notaxable"),
        "Total_Descuentos_Legales": liq.get("total_legal_discounts"),
        "Total_Otros_Descuentos": liq.get("total_other_discounts"),
        "Liquido_a_Pagar": liq.get("liquid_reach"),
        "Base_Imponible": liq.get("taxable_base"),
        "Cerrada": liq.get("closed"),
        "raw_payload": liq
    }
    return flattened

def explode_items_for_month(liq_list):
    """
    Recibe lista de liquidaciones (raw) y genera listado de items (filas).
    Cada item incluye referencia a Liquidacion_ID, ID_Empleado y campos del item.
    """
    items = []
    for liq in liq_list:
        lid = liq.get("liquidacion_id")
        pid = liq.get("person_id")
        eid = liq.get("employee_id")
        lines = liq.get("lines_settlement", []) or []
        for line in lines:
            items.append({
                "Liquidacion_ID": lid,
                "ID_Persona": pid,
                "ID_Empleado": eid,
                "type": line.get("type"),
                "income_type": line.get("income_type"),
                "subtype": line.get("subtype"),
                "name": line.get("name"),
                "amount": line.get("amount"),
                "taxable": line.get("taxable"),
                "imponible": line.get("imponible"),
                "anticipo": line.get("anticipo"),
                "credit_type": line.get("credit_type"),
                "institution": line.get("institution"),
                "description": line.get("description"),
                "code": line.get("code"),
                "item_code": line.get("item_code")
            })
    return items

# ------------------ Guardado en BD ------------------
def ensure_tables_and_indexes(engine):
    """
    Crea tablas básicas si no existen (con columnas mínimas).
    Optimización: Crea un índice único compuesto (Liquidacion_ID, Ano, Mes) para evitar duplicados en el mismo período.
    """
    insp = inspect(engine)
    with engine.begin() as conn:
        # Tabla payrolls (historical_settlements)
        if not insp.has_table(TABLE_PAYROLLS):
            logger.info(f"Creando tabla {TABLE_PAYROLLS} (primer uso)...")
            create_sql = f"""
            CREATE TABLE {TABLE_PAYROLLS} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                Liquidacion_ID BIGINT,
                ID_Persona BIGINT,
                ID_Empleado BIGINT,
                RUT VARCHAR(50),
                Periodo VARCHAR(16),
                Ano INT,
                Mes INT,
                Pay_Period DATE,
                Dias_Trabajados FLOAT,
                Dias_No_Trabajados FLOAT,
                Ingreso_Bruto DOUBLE,
                Ingreso_Neto DOUBLE,
                Ingreso_AFP DOUBLE,
                Ingreso_IPS DOUBLE,
                Total_Ingresos_Imponibles DOUBLE,
                Total_Ingresos_No_Imponibles DOUBLE,
                Total_Descuentos_Legales DOUBLE,
                Total_Otros_Descuentos DOUBLE,
                Liquido_a_Pagar DOUBLE,
                Base_Imponible DOUBLE,
                Cerrada BOOLEAN,
                raw_payload JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            conn.execute(text(create_sql))
            
            #  MEJORA: Índice único compuesto (Liquidacion_ID, Ano, Mes)
            conn.execute(text(f"CREATE UNIQUE INDEX ux_{TABLE_PAYROLLS}_liquidacion_period ON {TABLE_PAYROLLS} (Liquidacion_ID, Ano, Mes);"))
            
            # Índices adicionales para performance
            conn.execute(text(f"CREATE INDEX idx_{TABLE_PAYROLLS}_empleado ON {TABLE_PAYROLLS} (ID_Empleado);"))
            conn.execute(text(f"CREATE INDEX idx_{TABLE_PAYROLLS}_periodo ON {TABLE_PAYROLLS} (Pay_Period);"))
            
            logger.info(f"Tabla {TABLE_PAYROLLS} creada con índices corregidos.")
        else:
            # Si la tabla ya existe, corregir índices
            try:
                # Intenta eliminar el índice antiguo si existe
                conn.execute(text(f"DROP INDEX ux_{TABLE_PAYROLLS}_liquidacion_id ON {TABLE_PAYROLLS}"))
                logger.info(" Índice simple antiguo eliminado.")
            except Exception:
                pass  # No existía, no hay problema
            
            try:
                # Intenta crear el índice compuesto correcto
                conn.execute(text(f"CREATE UNIQUE INDEX ux_{TABLE_PAYROLLS}_liquidacion_period ON {TABLE_PAYROLLS} (Liquidacion_ID, Ano, Mes);"))
                logger.info(" Índice único compuesto corregido/creado.")
            except Exception as e:
                if "Duplicate key name" not in str(e):
                    logger.warning(f" No se pudo crear índice único: {e}")
                    
            # Asegurar índice para consultas por período
            try:
                conn.execute(text(f"CREATE INDEX idx_{TABLE_PAYROLLS}_ano_mes ON {TABLE_PAYROLLS} (Ano, Mes);"))
            except Exception:
                pass  # Ya existe

        # Tabla items (sin cambios necesarios)
        if not insp.has_table(TABLE_ITEMS):
            logger.info(f"Creando tabla {TABLE_ITEMS} (primer uso)...")
            create_items_sql = f"""
            CREATE TABLE {TABLE_ITEMS} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                Liquidacion_ID BIGINT,
                ID_Persona BIGINT,
                ID_Empleado BIGINT,
                item_type VARCHAR(50),
                income_type VARCHAR(100),
                subtype VARCHAR(100),
                name VARCHAR(255),
                amount DOUBLE,
                taxable BOOLEAN,
                imponible BOOLEAN,
                anticipo BOOLEAN,
                credit_type VARCHAR(100),
                institution VARCHAR(255),
                description TEXT,
                code VARCHAR(100),
                item_code VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_items_liquidacion (Liquidacion_ID)
            );
            """
            conn.execute(text(create_items_sql))
            logger.info(f"Tabla {TABLE_ITEMS} creada.")

def save_payrolls_batch_fixed(engine, df_payrolls):
    """
    Optimización: Usa una tabla temporal para un UPSERT atómico y eficiente.
    """
    if df_payrolls is None or df_payrolls.empty:
        logger.warning("   No hay filas de liquidaciones para insertar.")
        return 0

    df = df_payrolls.copy()
    
    # Pre-procesamiento de datos
    df = df.dropna(subset=['Liquidacion_ID', 'Año', 'Mes'])
    if df.empty:
        logger.warning("   No quedan filas válidas después del filtrado.")
        return 0
    
    df = df.rename(columns={
        "Período": "Periodo", "Año": "Ano", "Días_Trabajados": "Dias_Trabajados",
        "Días_No_Trabajados": "Dias_No_Trabajados", "Liquido_a_Pagar": "Liquido_a_Pagar",
        "Base_Imponible": "Base_Imponible"
    })
    
    # Convertir 'raw_payload' a string JSON
    if "raw_payload" in df.columns:
        df["raw_payload"] = df["raw_payload"].apply(lambda x: json.dumps(x) if x is not None else None)

    # Crear tabla temporal con timestamp único
    temp_table = f"{TABLE_PAYROLLS}_temp_{int(time.time())}_{os.getpid()}"
    
    inserted = 0
    with engine.begin() as conn:
        try:
            # 1. Crear tabla temporal con la misma estructura
            create_temp_sql = f"CREATE TEMPORARY TABLE {temp_table} LIKE {TABLE_PAYROLLS};"
            conn.execute(text(create_temp_sql))
            
            # 2. Insertar datos en tabla temporal
            df.to_sql(temp_table, con=conn, if_exists="append", index=False, method='multi')
            
            # 3.  MEJORA: UPSERT con ON DUPLICATE KEY UPDATE
            upsert_sql = f"""
            INSERT INTO {TABLE_PAYROLLS} 
            (Liquidacion_ID, ID_Persona, ID_Empleado, RUT, Periodo, Ano, Mes, Pay_Period, Dias_Trabajados,
             Dias_No_Trabajados, Ingreso_Bruto, Ingreso_Neto, Ingreso_AFP, Ingreso_IPS, Total_Ingresos_Imponibles,
             Total_Ingresos_No_Imponibles, Total_Descuentos_Legales, Total_Otros_Descuentos, Liquido_a_Pagar,
             Base_Imponible, Cerrada, raw_payload)
            SELECT Liquidacion_ID, ID_Persona, ID_Empleado, RUT, Periodo, Ano, Mes, Pay_Period, Dias_Trabajados,
                   Dias_No_Trabajados, Ingreso_Bruto, Ingreso_Neto, Ingreso_AFP, Ingreso_IPS, Total_Ingresos_Imponibles,
                   Total_Ingresos_No_Imponibles, Total_Descuentos_Legales, Total_Otros_Descuentos, Liquido_a_Pagar,
                   Base_Imponible, Cerrada, raw_payload 
            FROM {temp_table}
            ON DUPLICATE KEY UPDATE
                ID_Persona=VALUES(ID_Persona),
                ID_Empleado=VALUES(ID_Empleado),
                RUT=VALUES(RUT),
                Periodo=VALUES(Periodo),
                Pay_Period=VALUES(Pay_Period),
                Dias_Trabajados=VALUES(Dias_Trabajados),
                Dias_No_Trabajados=VALUES(Dias_No_Trabajados),
                Ingreso_Bruto=VALUES(Ingreso_Bruto),
                Ingreso_Neto=VALUES(Ingreso_Neto),
                Ingreso_AFP=VALUES(Ingreso_AFP),
                Ingreso_IPS=VALUES(Ingreso_IPS),
                Total_Ingresos_Imponibles=VALUES(Total_Ingresos_Imponibles),
                Total_Ingresos_No_Imponibles=VALUES(Total_Ingresos_No_Imponibles),
                Total_Descuentos_Legales=VALUES(Total_Descuentos_Legales),
                Total_Otros_Descuentos=VALUES(Total_Otros_Descuentos),
                Liquido_a_Pagar=VALUES(Liquido_a_Pagar),
                Base_Imponible=VALUES(Base_Imponible),
                Cerrada=VALUES(Cerrada),
                raw_payload=VALUES(raw_payload);
            """
            conn.execute(text(upsert_sql))
            inserted = len(df)
            
        except Exception as e:
            logger.error(f"     Error en save_payrolls_batch_fixed: {e}")
            logger.error(f"     Traceback completo: {traceback.format_exc()}")
            raise
        finally:
            # La tabla temporal se elimina automáticamente al cerrar la conexión
            pass
    
    logger.info(f"   Insertados/actualizados: {inserted} filas en {TABLE_PAYROLLS}")
    return inserted

def save_items_batch(engine, items_df):
    """
    Inserta items (lines_settlement) en tabla items.
    """
    if items_df is None or items_df.empty:
        logger.warning("   No hay items para insertar.")
        return 0

    df = items_df.copy()
    df = df.rename(columns={
        "type": "item_type"
    })
    cols_allowed = ["Liquidacion_ID","ID_Persona","ID_Empleado","item_type","income_type","subtype",
                    "name","amount","taxable","imponible","anticipo","credit_type","institution",
                    "description","code","item_code"]
    df = df[[c for c in cols_allowed if c in df.columns]]

    inserted = 0
    with engine.begin() as conn:
        # Usar to_sql en un solo llamado para mayor eficiencia
        try:
            df.to_sql(TABLE_ITEMS, con=conn, if_exists="append", index=False)
            inserted = len(df)
        except Exception as e:
            logger.error(f"     Error insertando items en {TABLE_ITEMS}: {e}")
            logger.error(f"     Traceback completo: {traceback.format_exc()}")

    logger.info(f"   Insertados: {inserted} filas en {TABLE_ITEMS}")
    return inserted

# ------------------ Periodos mensuales ------------------
def generate_monthly_periods(start_year=2019, start_month=1):
    periods = []
    current = datetime(start_year, start_month, 1)
    today = datetime.now()
    while current.year < today.year or (current.year == today.year and current.month <= today.month):
        periods.append({
            "year": current.year,
            "month": current.month,
            "date_param": f"01-{current.strftime('%m')}-{current.year}",
            "label": f"{current.strftime('%m')}-{current.year}"
        })
        current += relativedelta(months=1)
    return periods

# ------------------ FUNCIÓN DE VERIFICACIÓN ------------------
def verify_data_insertion(engine, year, month):
    """
     MEJORA: Función para verificar que los datos se insertaron correctamente.
    Muestra el total de registros y la cantidad de IDs distintos para validación.
    """
    with engine.connect() as conn:
        # Contar registros para el período
        count_total = conn.execute(text(f"""
            SELECT COUNT(*) FROM {TABLE_PAYROLLS} 
            WHERE Ano = {year} AND Mes = {month}
        """)).scalar()
        
        # Contar IDs distintos
        count_distinct_ids = conn.execute(text(f"""
            SELECT COUNT(DISTINCT Liquidacion_ID) FROM {TABLE_PAYROLLS} 
            WHERE Ano = {year} AND Mes = {month}
        """)).scalar()
        
        print(f"VERIFICACIÓN - Año: {year}, Mes: {month}")
        print(f"  Registros totales cargados: {count_total}")
        print(f"  IDs de liquidación distintos: {count_distinct_ids}")
        
        return count_total > 0 and count_total == count_distinct_ids

# ------------------ MAIN PROCESS ------------------
def main():
    logger.info("========== INICIANDO PROCESO ETL DE LIQUIDACIONES ==========")
    token = "Xegy8dVsa1H8SFfojJcwYtDL"
    base_url = "https://cramer.buk.cl/api/v1/chile/payroll_detail/month"

    try:
        engine = get_db_engine()
        ensure_tables_and_indexes(engine)
    except Exception as e:
        logger.error(f"Fallo al conectar o inicializar la base de datos: {e}")
        return

    # Para procesar todos los períodos, usa esta línea en su lugar:
    periods = generate_monthly_periods(2019, 1)
    
    logger.info(f"Periodos a procesar: {len(periods)}")

    total_processed = 0
    total_items = 0
    failed_periods = []

    for i, p in enumerate(periods, start=1):
        logger.info("\n" + "="*60)
        logger.info(f"Procesando período {i}/{len(periods)}: {p['label']}  (date param: {p['date_param']})")
        try:
            liqs = get_all_liquidaciones_data(base_url, token, p['date_param'])
            logger.info(f"   Liquidaciones obtenidas: {len(liqs)}")

            flat_rows = [flatten_liquidation(l) for l in liqs]
            df_liqs = pd.DataFrame(flat_rows)
            
            inserted = save_payrolls_batch_fixed(engine, df_liqs)
            total_processed += inserted

            #  MEJORA: Verificar inserción inmediatamente
            verification_result = verify_data_insertion(engine, p['year'], p['month'])
            if not verification_result:
                logger.error(f"   ADVERTENCIA: La verificación de datos para {p['label']} falló.")

            items = explode_items_for_month(liqs)
            df_items = pd.DataFrame(items)
            inserted_items = save_items_batch(engine, df_items)
            total_items += inserted_items

            time.sleep(0.3)

        except Exception as e:
            logger.error(f"Falló procesamiento para periodo {p['label']}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            failed_periods.append({"period": p['label'], "error": str(e)})
            continue

    logger.info("\n" + "="*60)
    logger.info("PROCESO FINALIZADO")
    logger.info(f"Total liquidaciones procesadas (aprox insertadas/actualizadas): {total_processed}")
    logger.info(f"Total items procesados (aprox insertados): {total_items}")
    if failed_periods:
        logger.warning("Períodos con error:")
        for f in failed_periods:
            logger.warning(f" - {f['period']}: {f['error']}")

#%%
if __name__ == "__main__":
    print("SISTEMA DE SINCRONIZACIÓN DE empleados - MODO PROGRAMADOR DE TAREAS")
    print("="*70)

    print("Ejecutando sincronización programada...")
    main()
    
    print("Tarea completada. El script finalizará automáticamente.")
    print("La próxima ejecución será programada por Windows.")

    sys.exit(0)