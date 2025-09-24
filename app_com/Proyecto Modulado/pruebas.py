import pymysql
from config.database import DB_CONFIG

try:
    connection = pymysql.connect(**DB_CONFIG)
    print("Conexión a la base de datos exitosa!")
    connection.close()
except pymysql.MySQLError as e:
    print(f"Error de conexión: {e}")