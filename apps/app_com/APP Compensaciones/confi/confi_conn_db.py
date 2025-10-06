# config/database.py
"""
Configuración de la base de datos
"""
import os
import sqlalchemy
from dotenv import load_dotenv
load_dotenv(override=True)

def get_database_config():
    """
    Obtiene la configuración de la base de datos
    """
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'test_db')
}

def configuracion_conexion(host=None, user=None, password=None, database=None):
    """
    Retorna la configuración de conexión a la base de datos, usando .env si no se
    especifican parámetros.
    """
    config = get_database_config()
    
    _host = host if host is not None else config['host']
    _user = user if user is not None else config['user']
    _password = password if password is not None else config['password']
    _database = database if database is not None else config['database']

    try:
        engine = sqlalchemy.create_engine(
            f"mysql+pymysql://{_user}:{_password}@{_host}:3306/{_database}")
        print("Conexión exitosa a la base de datos")
        return engine
        
    except Exception as e:
        print("Error de Conexión", f"No se pudo conectar a la base de datos: {e}")
        return None