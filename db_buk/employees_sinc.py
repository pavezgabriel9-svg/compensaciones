import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
import json

def get_all_employees_data(base_url, token):
    """
    Obtiene todos los empleados paginando a través de la API
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
            
            # Si recibimos menos de 100 registros, es la última página
            if len(current_data) < 100:
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error en la página {page}: {e}")
            break
    
    return all_data

def calculate_years(start_date):
    """
    Calcula años desde una fecha hasta hoy
    """
    if pd.isna(start_date) or start_date is None:
        return None
    
    try:
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        today = date.today()
        years = (today - start_date).days / 365.25
        return round(years, 1)
    except:
        return None

def process_employees_data(base_url, token):
    """
    Procesa los datos de empleados siguiendo la lógica del código M
    """
    
    # ===== CONFIGURACIÓN =====
    print("Obteniendo datos de empleados...")
    
    # ===== OBTENER DATOS =====
    all_employees_data = get_all_employees_data(base_url, token)
    
    if not all_employees_data:
        print("No se pudieron obtener datos de empleados")
        return pd.DataFrame()
    
    # Convertir a DataFrame
    df = pd.DataFrame(all_employees_data)
    print(f"Total de empleados obtenidos: {len(df)}")
    
    # ===== FILTROS =====
    # Filtrar empleados activos
    df_active = df[df['status'].str.lower().isin(['active', 'activo'])].copy()
    print(f"Empleados activos: {len(df_active)}")
    
    # Excluir personas específicas (IDs: 4804 y 9386)
    excluded_ids = [4804, 9386]
    df_filtered = df_active[
        ~((df_active['id'].isin(excluded_ids)) | 
          (df_active['person_id'].isin(excluded_ids)))
    ].copy()
    print(f"Empleados después de exclusiones: {len(df_filtered)}")
    
    # ===== EXPANDIR DATOS ANIDADOS =====
    
    # Expandir current_job
    if 'current_job' in df_filtered.columns:
        job_df = pd.json_normalize(df_filtered['current_job'].dropna())
        job_columns = ['role', 'boss', 'base_wage', 'area_id', 'start_date', 
                      'end_date', 'contract_type', 'cost_center', 'weekly_hours']
        
        for col in job_columns:
            if col in job_df.columns:
                df_filtered[col] = job_df[col].values
    
    # Expandir role
    if 'role' in df_filtered.columns:
        role_df = pd.json_normalize(df_filtered['role'].dropna())
        if 'id' in role_df.columns:
            df_filtered['role_id'] = role_df['id'].values
        if 'name' in role_df.columns:
            df_filtered['nombre_rol'] = role_df['name'].values
        if 'role_family' in role_df.columns:
            df_filtered['role_family'] = role_df['role_family'].values
    
    # Expandir role_family
    if 'role_family' in df_filtered.columns:
        family_df = pd.json_normalize(df_filtered['role_family'].dropna())
        if 'id' in family_df.columns:
            df_filtered['family_id'] = family_df['id'].values
        if 'name' in family_df.columns:
            df_filtered['nombre_familia'] = family_df['name'].values
    
    # Expandir boss
    if 'boss' in df_filtered.columns:
        boss_df = pd.json_normalize(df_filtered['boss'].dropna())
        boss_columns = {'id': 'id_jefe', 'person_id': 'person_id_jefe', 'rut': 'rut_jefe'}
        for orig_col, new_col in boss_columns.items():
            if orig_col in boss_df.columns:
                df_filtered[new_col] = boss_df[orig_col].values
    
    # ===== RENOMBRAR COLUMNAS =====
    column_mapping = {
        'id': 'ID_Empleado',
        'person_id': 'ID_Persona', 
        'full_name': 'Nombre_Completo',
        'rut': 'RUT',
        'gender': 'Genero',
        'city': 'Ciudad',
        'region': 'Region',
        'birthday': 'Fecha_Nacimiento',
        'active_since': 'Fecha_Activacion',
        'status': 'Estado',
        'area_id': 'ID_Area',
        'start_date': 'Fecha_Inicio_Contrato',
        'end_date': 'Fecha_Fin_Contrato',
        'contract_type': 'Tipo_Contrato',
        'cost_center': 'Centro_Costo',
        'weekly_hours': 'Horas_Semanales',
        'role_id': 'ID_Rol',
        'nombre_rol': 'Nombre_Rol',
        'family_id': 'ID_Familia_Rol',
        'nombre_familia': 'Nombre_Familia_Rol',
        'id_jefe': 'ID_Jefe',
        'person_id_jefe': 'Person_ID_Jefe',
        'rut_jefe': 'RUT_Jefe',
        'base_wage': 'Sueldo_Base'
    }
    
    # Renombrar solo las columnas que existen
    existing_columns = {k: v for k, v in column_mapping.items() if k in df_filtered.columns}
    df_renamed = df_filtered.rename(columns=existing_columns)
    
    # ===== OBTENER NOMBRE DEL JEFE =====
    # Self-join para obtener nombre del jefe
    if 'ID_Jefe' in df_renamed.columns and 'ID_Empleado' in df_renamed.columns:
        # Crear diccionario de empleados para lookup
        employee_lookup = df_renamed.set_index('ID_Empleado')['Nombre_Completo'].to_dict()
        df_renamed['Nombre_Jefe'] = df_renamed['ID_Jefe'].map(employee_lookup)
        
        # Fallback con Person_ID si no se encontró por ID_Empleado
        if 'Person_ID_Jefe' in df_renamed.columns and 'ID_Persona' in df_renamed.columns:
            person_lookup = df_renamed.set_index('ID_Persona')['Nombre_Completo'].to_dict()
            mask = df_renamed['Nombre_Jefe'].isna()
            df_renamed.loc[mask, 'Nombre_Jefe'] = df_renamed.loc[mask, 'Person_ID_Jefe'].map(person_lookup)
    
    # ===== CÁLCULOS =====
    
    # Calcular edad
    if 'Fecha_Nacimiento' in df_renamed.columns:
        df_renamed['Edad'] = df_renamed['Fecha_Nacimiento'].apply(calculate_years)
    
    # Calcular años de servicio
    if 'Fecha_Activacion' in df_renamed.columns:
        df_renamed['Anos_Servicio'] = df_renamed['Fecha_Activacion'].apply(calculate_years)
    
    # Calcular antigüedad en cargo
    if 'Fecha_Inicio_Contrato' in df_renamed.columns:
        df_renamed['Antiguedad_Cargo'] = df_renamed['Fecha_Inicio_Contrato'].apply(calculate_years)
    elif 'Fecha_Activacion' in df_renamed.columns:
        df_renamed['Antiguedad_Cargo'] = df_renamed['Fecha_Activacion'].apply(calculate_years)
    
    # Rangos de edad
    if 'Edad' in df_renamed.columns:
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
        
        df_renamed['Rango_Edad'] = df_renamed['Edad'].apply(age_range)
    
    # Rangos de antigüedad
    if 'Anos_Servicio' in df_renamed.columns:
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
        
        df_renamed['Rango_Antiguedad'] = df_renamed['Anos_Servicio'].apply(service_range)
    
    # Salario por hora
    if 'Horas_Semanales' in df_renamed.columns and 'Sueldo_Base' in df_renamed.columns:
        df_renamed['Salario_Por_Hora'] = np.where(
            (df_renamed['Horas_Semanales'] > 0) & (df_renamed['Sueldo_Base'].notna()),
            (df_renamed['Sueldo_Base'] / (df_renamed['Horas_Semanales'] * 4.33)).round(0),
            None
        )
    
    # Bandas salariales
    if 'Sueldo_Base' in df_renamed.columns:
        valid_salaries = df_renamed['Sueldo_Base'].dropna()
        if len(valid_salaries) > 0:
            p25 = valid_salaries.quantile(0.25)
            p50 = valid_salaries.quantile(0.50)
            p75 = valid_salaries.quantile(0.75)
            p90 = valid_salaries.quantile(0.90)
            
            def salary_band(salary):
                if pd.isna(salary):
                    return "No disponible"
                elif salary <= p25:
                    return "Bajo (≤P25)"
                elif salary <= p50:
                    return "Medio-Bajo (P25-P50)"
                elif salary <= p75:
                    return "Medio-Alto (P50-P75)"
                elif salary <= p90:
                    return "Alto (P75-P90)"
                else:
                    return "Muy Alto (>P90)"
            
            df_renamed['Banda_Salarial'] = df_renamed['Sueldo_Base'].apply(salary_band)
    
    # Identificar jefes
    if 'ID_Jefe' in df_renamed.columns:
        all_boss_ids = set()
        if 'ID_Jefe' in df_renamed.columns:
            all_boss_ids.update(df_renamed['ID_Jefe'].dropna().values)
        if 'Person_ID_Jefe' in df_renamed.columns:
            all_boss_ids.update(df_renamed['Person_ID_Jefe'].dropna().values)
        
        df_renamed['Es_Jefe'] = (
            df_renamed['ID_Empleado'].isin(all_boss_ids) | 
            df_renamed['ID_Persona'].isin(all_boss_ids)
        )
    
    # ===== SELECCIÓN FINAL =====
    final_columns = [
        'ID_Empleado', 'ID_Persona', 'RUT', 'Nombre_Completo', 'Genero',
        'Edad', 'Rango_Edad', 'Anos_Servicio', 'Rango_Antiguedad', 'Antiguedad_Cargo',
        'Estado', 'ID_Area', 'Tipo_Contrato', 'Centro_Costo', 'Horas_Semanales',
        'ID_Rol', 'Nombre_Rol', 'Sueldo_Base', 'Es_Jefe', 'Nombre_Jefe', 
        'ID_Jefe', 'Person_ID_Jefe', 'RUT_Jefe'
    ]
    
    # Seleccionar solo columnas que existen
    available_columns = [col for col in final_columns if col in df_renamed.columns]
    df_final = df_renamed[available_columns].copy()
    
    # Renombrar columnas finales
    final_rename = {
        'Nombre_Completo': 'Nombre',
        'Genero': 'Género', 
        'Anos_Servicio': 'Años de Servicio',
        'Rango_Edad': 'Rango de Edad',
        'Rango_Antiguedad': 'Rango de Antigüedad',
        'Antiguedad_Cargo': 'Antigüedad en Cargo',
        'Tipo_Contrato': 'Tipo de Contrato',
        'Centro_Costo': 'Centro de Costo',
        'Horas_Semanales': 'Horas Semanales',
        'Nombre_Rol': 'Cargo',
        'Sueldo_Base': 'Sueldo Base',
        'Es_Jefe': 'Es Jefe',
        'Nombre_Jefe': 'Jefe Directo'
    }
    
    # Renombrar solo columnas existentes
    existing_renames = {k: v for k, v in final_rename.items() if k in df_final.columns}
    df_final = df_final.rename(columns=existing_renames)
    
    return df_final

# ===== FUNCIÓN PRINCIPAL =====
def main():
    # Configuración
    base_url = "https://cramer.buk.cl/api/v1/chile/employees"
    token = "Xegy8dVsa1H8SFfojJcwYtDL"
    
    # Procesar datos
    df_result = process_employees_data(base_url, token)
    
    # Mostrar resultados
    print(f"\nDataFrame final con {len(df_result)} empleados")
    print(f"Columnas: {list(df_result.columns)}")

    # Guardar a Excel
    df_result.to_excel('empleados_procesados.xlsx', index=False)
    print("Datos guardados en 'empleados_procesados.xlsx'")

    return df_result

# Ejemplo de uso (comentado para no ejecutar automáticamente)
df_empleados = main()
print(df_empleados.head())

# print("Código Python creado exitosamente!")
# print("\nPara usar el código:")
# print("1. Instala las dependencias: pip install pandas requests numpy")
# print("2. Ejecuta: df_empleados = main()")
# print("3. Los datos se guardarán en 'empleados_procesados.csv'")