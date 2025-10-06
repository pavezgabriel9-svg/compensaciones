# controllers/personal_file_controller.py

import pandas as pd
from datetime import datetime

def preparar_datos_ficha(rut, data_df, employees_df, settlements_df):
    """
    Filtra, procesa y prepara todos los datos necesarios para la ficha de una persona.
    """
    if data_df is None or data_df.empty:
        print(f"DataFrame principal vacío.")
        return None, None

    df_persona_base = data_df[data_df["rut"] == rut].copy()
    if df_persona_base.empty:
        print(f"No se encontraron datos para el rut: {rut}")
        return None, None
    df_persona_base.sort_values(by="start_date", inplace=True)
    df_persona_base['start_month'] = df_persona_base['start_date'].dt.to_period('M').dt.to_timestamp()
    df_persona_base.set_index('start_month', inplace=True)

    # 2. Obtener datos de liquidaciones
    df_liquidaciones_persona = pd.DataFrame()
    if settlements_df is not None and not settlements_df.empty:
        df_liquidaciones_persona = settlements_df[settlements_df["rut"] == rut].copy()
        if not df_liquidaciones_persona.empty:
            df_liquidaciones_persona.set_index('Pay_Period', inplace=True)

    # 3. Crear un rango de fechas completo para el gráfico
    active_since = df_persona_base['active_since'].min()
    start_date = active_since if pd.notna(active_since) else df_persona_base.index.min()
    end_date = datetime.now()
    df_completo = pd.DataFrame(index=pd.date_range(start=start_date, end=end_date, freq='MS'))
    
    # 4. Unir datos de sueldo base y líquido
    df_completo = df_completo.merge(df_persona_base[['base_wage']], left_index=True, right_index=True, how='left')
    df_completo = df_completo.merge(df_liquidaciones_persona[['Liquido_a_Pagar']], left_index=True, right_index=True, how='left')

    # Propagar el último valor de sueldo base conocido hacia adelante
    df_completo['base_wage'] = df_completo['base_wage'].ffill()

    # Resetear índice y añadir columnas de fecha
    df_completo.reset_index(inplace=True)
    df_completo.rename(columns={'index': 'Fecha'}, inplace=True)
    df_completo['years'] = df_completo['Fecha'].dt.year
    df_completo['month'] = df_completo['Fecha'].dt.month

    # Replicar datos de la última fila para la tarjeta de información
    last_row_info = df_persona_base.iloc[-1].copy()
    for col in last_row_info.index:
        if col not in df_completo.columns:
            df_completo[col] = last_row_info[col]

    # 5. Obtener datos adicionales del empleado desde el DataFrame de empleados
    emp_info = None
    if employees_df is not None:
        emp_data = employees_df[employees_df["rut"] == rut]
        if not emp_data.empty:
            emp_info = emp_data.iloc[0]
            
    return df_completo, emp_info