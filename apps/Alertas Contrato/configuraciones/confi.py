
# Entorno macOS
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "conexion_buk"

# Entorno Windows
# DB_HOST = "192.168.245.33"
# DB_USER = "compensaciones_rrhh"
# DB_PASSWORD = "_Cramercomp2025_"
# DB_NAME = "rrhh_app"


def get_database_config():
    return {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME
    }

