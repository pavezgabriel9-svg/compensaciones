# Ejecutar este script UNA VEZ antes de reiniciar el ETL
from sqlalchemy import create_engine, text

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "conexion_buk"

def clean_all_tables():
    conn_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    engine = create_engine(conn_str, pool_recycle=3600)
    
    with engine.begin() as conn:
        print("🧹 Limpiando todas las tablas...")
        conn.execute(text("TRUNCATE TABLE historical_settlements"))
        conn.execute(text("TRUNCATE TABLE historical_settlement_items"))
        print("✅ Tablas limpiadas completamente")

if __name__ == "__main__":
    clean_all_tables()