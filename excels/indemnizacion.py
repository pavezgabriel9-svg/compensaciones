# %%
import pandas as pd
import numpy as np
from datetime import datetime

# %%
df = pd.read_excel("C:\\Users\\gpavez\\Desktop\\base indemnización.xlsx")
print(f"Registros originales: {len(df)}")

# %%
# Eliminar duplicados por RUT (mantener el primer registro)
print(f"RUTs duplicados encontrados: {df.duplicated(subset=['RUT']).sum()}")
df = df.drop_duplicates(subset=['RUT'], keep='first')
print(f"Registros después de eliminar duplicados: {len(df)}")

# %%
# Limpiar columnas innecesarias
df_limpio = df.drop(columns=['Género','Fecha_Nacimiento','Fecha_Activacion',
                             'Fecha_Inicio_Contrato','ID_Area','Nombre_Area',
                             'Primer_Nivel','Segundo_Nivel'], errors="ignore")
df_limpio = df_limpio.rename(columns={"Años de Servicio": "Anios de Servicio"})

print("Columnas finales:", df_limpio.columns.tolist())

# %%
def obtener_valor_uf():
    """Valor UF actualizado - verificar valor actual"""
    return 39_429  # Actualizar con valor real de agosto 2025

def calcular_indemnizacion_empleado(sueldo_base, anos_servicio, con_clausula_no_competencia=True):
    """Calcula indemnización según política Cramer (estricta, sin regla especial de 65 años)"""
    
    if anos_servicio < 4:
        return {
            'elegible': False,
            'rango': 'No elegible',
            'indemnizacion_neta': 0
        }
    
    valor_uf = obtener_valor_uf()
    tope_uf_90 = 90 * valor_uf
    
    # Determinar rango correctamente
    if 4 <= anos_servicio < 20:
        rango = 'A'
        sueldo_con_tope = min(sueldo_base, tope_uf_90)
        anos_para_calculo = min(anos_servicio, 11)
    elif 20 <= anos_servicio < 25:
        rango = 'B'
        sueldo_con_tope = min(sueldo_base, tope_uf_90)
        anos_para_calculo = min(anos_servicio, 16)
    else:  # 25 o más años
        rango = 'C'
        if con_clausula_no_competencia:
            sueldo_con_tope = sueldo_base  # sin tope
            anos_para_calculo = anos_servicio
        else:
            sueldo_con_tope = min(sueldo_base, tope_uf_90)
            anos_para_calculo = min(anos_servicio, 16)
    
    indemnizacion_bruta = sueldo_con_tope * anos_para_calculo
    descuento_cesantia = indemnizacion_bruta * 0.024
    indemnizacion_neta = indemnizacion_bruta - descuento_cesantia
    
    return {
        'elegible': True,
        'rango': rango,
        'sueldo_con_tope': sueldo_con_tope,
        'anos_para_calculo': anos_para_calculo,
        'indemnizacion_neta': indemnizacion_neta
    }


def calcular_proyeccion_65_anos(sueldo_base, anos_servicio_actual, edad_actual, con_clausula_no_competencia=True):
    """Proyecta indemnización a los 65 (solo depende de antigüedad real, sin regla especial)"""
    
    if edad_actual >= 64:
        return {
            'aplicable': False,
            'indemnizacion_proyectada': 0,
            'anos_servicio_proyectados': anos_servicio_actual,
            'anos_adicionales': 0,
            'rango_proyectado': None
        }
    
    # Años adicionales hasta cumplir 65
    anos_adicionales = 64 - edad_actual
    anos_servicio_proyectados = anos_servicio_actual + anos_adicionales
    
    # Recalcular indemnización usando la antigüedad proyectada
    resultado = calcular_indemnizacion_empleado(
        sueldo_base, anos_servicio_proyectados, con_clausula_no_competencia
    )
    
    return {
        'aplicable': True,
        'rango_proyectado': resultado['rango'],
        'anos_servicio_proyectados': anos_servicio_proyectados,
        'anos_adicionales': anos_adicionales,
        'indemnizacion_proyectada': resultado['indemnizacion_neta']
    }

# %%
print("Calculando indemnizaciones actuales y proyecciones...")

resultados_actuales = []
resultados_proyeccion = []

for index, row in df_limpio.iterrows():
    resultado_actual = calcular_indemnizacion_empleado(
        sueldo_base=row['Sueldo Base'],
        anos_servicio=row['Anios de Servicio'],
        con_clausula_no_competencia=True
    )
    resultados_actuales.append(resultado_actual)
    
    resultado_proyeccion = calcular_proyeccion_65_anos(
        sueldo_base=row['Sueldo Base'],
        anos_servicio_actual=row['Anios de Servicio'],
        edad_actual=row['Edad'],
        con_clausula_no_competencia=True
    )
    resultados_proyeccion.append(resultado_proyeccion)

# %%
df_limpio['Rango_Antiguedad'] = [r['rango'] for r in resultados_actuales]
df_limpio['Elegible'] = [r['elegible'] for r in resultados_actuales]
df_limpio['Indemnizacion_Neta_Actual'] = [r['indemnizacion_neta'] for r in resultados_actuales]
df_limpio['Proyeccion_Aplicable'] = [r['aplicable'] for r in resultados_proyeccion]
df_limpio['Anos_Adicionales_Hasta_65'] = [r.get('anos_adicionales', 0) for r in resultados_proyeccion]
df_limpio['Anos_Servicio_A_Los_65'] = [r.get('anos_servicio_proyectados', 0) for r in resultados_proyeccion]
df_limpio['Indemnizacion_Neta_A_Los_65'] = [r.get('indemnizacion_proyectada', 0) for r in resultados_proyeccion]
df_limpio['Diferencia_Proyeccion'] = df_limpio['Indemnizacion_Neta_A_Los_65'] - df_limpio['Indemnizacion_Neta_Actual']

# =========================================================
# Con vs Sin cláusula (sin regla especial)
# =========================================================
indem_con = []
indem_sin = []

for idx, row in df_limpio.iterrows():
    calc_con = calcular_proyeccion_65_anos(
        sueldo_base=row['Sueldo Base'],
        anos_servicio_actual=row['Anios de Servicio'],
        edad_actual=row['Edad'],
        con_clausula_no_competencia=True
    )
    calc_sin = calcular_proyeccion_65_anos(
        sueldo_base=row['Sueldo Base'],
        anos_servicio_actual=row['Anios de Servicio'],
        edad_actual=row['Edad'],
        con_clausula_no_competencia=False
    )
    indem_con.append(calc_con)
    indem_sin.append(calc_sin)

df_limpio['Indemnizacion_Con_Clausula'] = [r.get('indemnizacion_proyectada', 0) for r in indem_con]
df_limpio['Indemnizacion_Sin_Clausula'] = [r.get('indemnizacion_proyectada', 0) for r in indem_sin]
df_limpio['Diferencia_Clausula'] = df_limpio['Indemnizacion_Con_Clausula'] - df_limpio['Indemnizacion_Sin_Clausula']

# %%
print(f"\n=== ESTADÍSTICAS FINALES ===")
print(f"Total empleados procesados: {len(df_limpio)}")
print(f"Empleados elegibles para indemnización actual: {df_limpio['Elegible'].sum()}")
print(f"Empleados con proyección aplicable: {df_limpio['Proyeccion_Aplicable'].sum()}")
print(f"Empleados ya con 65+ años: {(df_limpio['Edad'] >= 65).sum()}")

print(f"\n=== MONTOS PROMEDIO ===")
print(f"Indemnización actual promedio: ${df_limpio[df_limpio['Elegible']]['Indemnizacion_Neta_Actual'].mean():,.0f}")
print(f"Indemnización proyectada promedio: ${df_limpio[df_limpio['Proyeccion_Aplicable']]['Indemnizacion_Neta_A_Los_65'].mean():,.0f}")
print(f"Diferencia promedio: ${df_limpio[df_limpio['Proyeccion_Aplicable']]['Diferencia_Proyeccion'].mean():,.0f}")

# %%
archivo_salida = "C:\\Users\\gpavez\\Desktop\\Indemnizacion_Calculada_SinRegla65.xlsx"
df_limpio.to_excel(archivo_salida, index=False)
print(f"\nResultados guardados en: {archivo_salida}")

# =========================================================
# Top 5 beneficio proyectado
# =========================================================
print("\n=== TOP 5 EMPLEADOS CON MAYOR BENEFICIO PROYECTADO ===")
top_beneficio = df_limpio[df_limpio['Proyeccion_Aplicable']].nlargest(5, 'Diferencia_Proyeccion')

for idx, row in top_beneficio.iterrows():
    print(f"RUT: {row['RUT']}, Edad: {int(row['Edad'])}, Años servicio: {int(row['Anios de Servicio'])}")
    print(f"  Actual: ${row['Indemnizacion_Neta_Actual']:,.0f}")
    print(f"  A los 65 CON cláusula: ${row['Indemnizacion_Con_Clausula']:,.0f}")
    print(f"  A los 65 SIN cláusula: ${row['Indemnizacion_Sin_Clausula']:,.0f}")
    print(f"  Diferencia actual vs 65: ${row['Diferencia_Proyeccion']:,.0f}")
    print(f"  Diferencia cláusula vs sin cláusula: ${row['Diferencia_Clausula']:,.0f}")
    print(f"  Años adicionales: {int(row['Anos_Adicionales_Hasta_65'])}")
    print("---")
