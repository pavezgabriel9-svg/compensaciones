# %%
import pymysql
import pandas as pd

# Configuración BD (misma que tienes en tu código original)
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

pais = "CHILE" # "PERU" o "CHILE"

# %%
def conectar_y_extraer_datos():
    """
    Conecta a la base de datos y extrae las columnas específicas en un DataFrame
    """
    try:
        print("🚀 Conectando a MySQL...")
        
        # Establecer conexión
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4'
        )

        print("Conexión exitosa.")

        if "PERU" in pais:
            query_personas = """
                SELECT
                    empleado.full_name AS nombre,
                    empleado.document_number AS dni,
                    empleado.name_role AS cargo,
                    empleado.base_wage AS sueldo_base,
                    jefe.full_name AS nombre_jefe,
                    jefe.name_role AS cargo_jefe,
                    -- Calcula la edad en años
                    TIMESTAMPDIFF(YEAR, empleado.birthday, CURDATE()) AS edad,
                    -- Calcula el tiempo en la empresa en años
                    TIMESTAMPDIFF(YEAR, empleado.active_since, CURDATE()) AS años_en_la_empresa,
                    -- Calcula el tiempo en meses
                    TIMESTAMPDIFF(MONTH, empleado.active_since, CURDATE()) AS meses_en_la_empresa
                FROM
                    rrhh_app.employees_peru AS empleado
                LEFT JOIN
                    rrhh_app.employees_peru AS jefe ON empleado.dni_boss = jefe.document_number
                WHERE
                    empleado.status = "activo";
                """
            query_cargos = """
                SELECT
                    name_role AS cargo,
                    MIN(base_wage) AS sueldo_base_minimo,
                    MAX(base_wage) AS sueldo_base_maximo
                FROM
                    rrhh_app.employees_peru
                GROUP BY
                    name_role
                ORDER BY
                    name_role;
            """
        elif "CHILE" in pais:
            query_personas = """
                SELECT
                    empleado.full_name AS nombre,
                    empleado.rut,
                    empleado.name_role AS cargo,
                    empleado.base_wage AS sueldo_base,
                    jefe.full_name AS nombre_jefe,
                    jefe.name_role AS cargo_jefe,
                    -- Calcula la edad en años
                    TIMESTAMPDIFF(YEAR, empleado.birthday, CURDATE()) AS edad,
                    -- Calcula el tiempo en la empresa en años
                    TIMESTAMPDIFF(YEAR, empleado.active_since, CURDATE()) AS años_en_la_empresa,
                    -- Calcula el tiempo en meses
                    TIMESTAMPDIFF(MONTH, empleado.active_since, CURDATE()) AS meses_en_la_empresa
                FROM
                    rrhh_app.employees AS empleado
                LEFT JOIN
                    rrhh_app.employees AS jefe ON empleado.rut_boss = jefe.rut
                WHERE
                    empleado.status = "activo";
                """
            query_cargos = """
                SELECT
                    name_role AS cargo,
                    MIN(base_wage) AS sueldo_base_minimo,
                    MAX(base_wage) AS sueldo_base_maximo
                FROM
                    rrhh_app.employees
                GROUP BY
                    name_role
                ORDER BY
                    name_role;
            """
        
        # Crear DataFrame directamente desde la query
        df_personas = pd.read_sql(query_personas, conexion)
        df_cargos = pd.read_sql(query_cargos, conexion)

        print(f"📋 Columnas disponibles en df_personas: {list(df_personas.columns)}")
        print(f"📋 Columnas disponibles en df_cargos: {list(df_cargos.columns)}")
        # Cerrar conexión
        conexion.close()
        print("✅ Conexión cerrada correctamente.")

        return df_personas, df_cargos
        
    except Exception as e:
        print(f"❌ Error al conectar o extraer datos: {e}")
        return None

# %%

def export_query_to_excel(df_personas, df_cargos):
    # Exportar DataFrame a Excel
    if "PERU" in pais:
        ruta_archivo = "reporte_personas_cargos_peru.xlsx"
    elif "CHILE" in pais:
        ruta_archivo = "reporte_personas_cargos_chile.xlsx"
    with pd.ExcelWriter(ruta_archivo, engine="openpyxl") as writer:
        df_personas.to_excel(writer, sheet_name="Personas", index=False)   
        df_cargos.to_excel(writer, sheet_name="Cargos", index=False)  
    print(f"Archivo Excel creado en: {ruta_archivo}")


# %%
if __name__ == "__main__":
    df_personas, df_cargos = conectar_y_extraer_datos()
    if df_personas is not None and df_cargos is not None:
        export_query_to_excel(df_personas, df_cargos)


# %%



