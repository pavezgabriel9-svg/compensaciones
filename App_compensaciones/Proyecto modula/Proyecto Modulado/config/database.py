# config/database.py
"""
Configuración de la base de datos
"""
import os

# Configuración por defecto (desarrollo local)
DEFAULT_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'cancionanimal',
    'database': 'conexion_buk',
    'charset': 'utf8mb4'
}

# Configuración de producción (comentada)
# PRODUCTION_CONFIG = {
#     'host': '192.168.245.33',
#     'user': 'compensaciones_rrhh',
#     'password': '_Cramercomp2025_',
#     'database': 'rrhh_app',
#     'charset': 'utf8mb4'
# }

# def get_database_config():
#     """
#     Obtiene la configuración de la base de datos según el entorno
#     """
#     env = os.getenv('DASHBOARD_ENV', 'development')
    
#     if env.lower() == 'production':
#         return PRODUCTION_CONFIG
#     else:
#         return DEFAULT_CONFIG

# Exportar configuración activa
#DB_CONFIG = get_database_config()

DB_CONFIG = DEFAULT_CONFIG