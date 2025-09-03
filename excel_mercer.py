import requests
import pandas as pd
import time
from datetime import datetime
import json

# Configuración API
URL_EMPLOYEES = "https://cramer.buk.cl/api/v1/chile/employees"
URL_PAYROLL = "https://cramer.buk.cl/api/v1/chile/payroll_detail/month"
TOKEN = "Xegy8dVsa1H8SFfojJcwYtDL"

def obtener_todos_los_empleados():
    """Obtiene todos los empleados con paginación mejorada"""
    headers = {"auth_token": TOKEN}
    empleados = []
    url_actual = URL_EMPLOYEES
    page = 1
    
    print("🚀 Obteniendo empleados...")
    
    while url_actual:
        try:
            response = requests.get(url_actual, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            current_data = data.get('data', [])
            empleados.extend(current_data)
            print(f"📄 Página {page}: {len(current_data)} empleados")
            
            # Usar paginación de la respuesta
            pagination = data.get('pagination', {})
            url_actual = pagination.get('next')
            page += 1
            
            time.sleep(0.3)  # Pausa más corta
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
    
    print(f"✅ Total empleados: {len(empleados)}")
    return empleados

def obtener_liquidaciones(fecha="30-08-2025"):
    """Obtiene liquidaciones con paginación mejorada"""
    headers = {"auth_token": TOKEN}
    liquidaciones = []
    url_actual = f"{URL_PAYROLL}?date={fecha}"
    page = 1
    
    print(f"🚀 Obteniendo liquidaciones para {fecha}...")
    
    while url_actual:
        try:
            response = requests.get(url_actual, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            current_data = data.get('data', [])
            liquidaciones.extend(current_data)
            print(f"📄 Página {page}: {len(current_data)} liquidaciones")
            
            # Usar paginación de la respuesta
            pagination = data.get('pagination', {})
            url_actual = pagination.get('next')
            page += 1
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ Error liquidaciones: {e}")
            break
    
    print(f"✅ Total liquidaciones: {len(liquidaciones)}")
    return liquidaciones

def crear_diccionario_empleados(empleados):
    """Crea diccionario para búsqueda rápida de empleados por ID"""
    return {emp.get('id'): emp for emp in empleados}

def extraer_componentes_compensacion(liquidacion):
    """Extrae y clasifica componentes de compensación"""
    componentes = {
        'sueldo_base': 0, 'gratificacion': 0, 'asignaciones': 0,
        'aguinaldos': 0, 'bonos_fijos': 0, 'bonos_variables': 0,
        'comisiones': 0, 'horas_extras': 0, 'otros_ingresos': 0
    }
    
    for linea in liquidacion.get('lines_settlement', []):
        nombre = linea.get('name', '').lower()
        tipo = linea.get('type', '').lower()
        monto = linea.get('amount', 0)
        
        if tipo != 'haber' or monto <= 0:
            continue
            
        # Clasificación de componentes
        if any(x in nombre for x in ['sueldo', 'base', 'wage']):
            componentes['sueldo_base'] += monto
        elif any(x in nombre for x in ['gratificacion', 'gratif']):
            componentes['gratificacion'] += monto
        elif any(x in nombre for x in ['asignacion', 'asig']):
            componentes['asignaciones'] += monto
        elif 'aguinaldo' in nombre:
            componentes['aguinaldos'] += monto
        elif 'comision' in nombre:
            componentes['comisiones'] += monto
        elif any(x in nombre for x in ['hora extra', 'overtime']):
            componentes['horas_extras'] += monto
        elif 'bono' in nombre:
            if 'variable' in nombre:
                componentes['bonos_variables'] += monto
            else:
                componentes['bonos_fijos'] += monto
        else:
            componentes['otros_ingresos'] += monto
    
    return componentes

def extraer_detalle_liquidacion(liquidacion):
    """Extrae información detallada de la liquidación incluyendo haberes, descuentos y aportes"""
    detalle = {
        # 💰 Ingresos principales
        'income_gross': liquidacion.get('income_gross', 0),
        'income_net': liquidacion.get('income_net', 0),
        'income_afp': liquidacion.get('income_afp', 0),
        'income_ips': liquidacion.get('income_ips', 0),
        'total_income_taxable': liquidacion.get('total_income_taxable', 0),
        'total_income_notaxable': liquidacion.get('total_income_notaxable', 0),
        'closed': liquidacion.get('closed', False),
        
        # 📉 Descuentos
        'total_legal_discounts': liquidacion.get('total_legal_discounts', 0),
        'total_other_discounts': liquidacion.get('total_other_discounts', 0),
        'taxable_base': liquidacion.get('taxable_base', 0),
        
        # 📋 Contadores de líneas por tipo
        'total_haberes': 0,
        'total_descuentos': 0,
        'total_aportes': 0,
        'total_informativos': 0,
        
        # 💡 Detalle de conceptos imponibles vs no imponibles
        'haberes_imponibles': 0,
        'haberes_no_imponibles': 0,
        'descuentos_legales': 0,
        'descuentos_voluntarios': 0
    }
    
    # Procesar líneas de liquidación
    for linea in liquidacion.get('lines_settlement', []):
        tipo = linea.get('type', '').lower()
        monto = linea.get('amount', 0)
        imponible = linea.get('taxable', False) or linea.get('imponible', False)
        
        # Contar por tipo
        if tipo == 'haber':
            detalle['total_haberes'] += 1
            if imponible:
                detalle['haberes_imponibles'] += monto
            else:
                detalle['haberes_no_imponibles'] += monto
                
        elif tipo == 'descuento':
            detalle['total_descuentos'] += 1
            # Clasificar descuentos (esto puede necesitar ajuste según los nombres)
            nombre = linea.get('name', '').lower()
            if any(x in nombre for x in ['afp', 'fonasa', 'isapre', 'seguro', 'impuesto']):
                detalle['descuentos_legales'] += monto
            else:
                detalle['descuentos_voluntarios'] += monto
                
        elif tipo == 'aporte':
            detalle['total_aportes'] += 1
            
        elif tipo == 'informativo':
            detalle['total_informativos'] += 1
    
    return detalle

def generar_excel_mercer(empleados, liquidaciones):
    """Genera Excel final para Mercer con optimizaciones"""
    print("🚀 Generando Excel para Mercer...")
    
    # 🔥 OPTIMIZACIÓN 1: Crear diccionario de empleados para búsqueda rápida
    empleados_dict = crear_diccionario_empleados(empleados)
    
    # 🔥 OPTIMIZACIÓN 2: Filtrar solo empleados activos desde el inicio
    empleados_activos = [emp for emp in empleados if emp.get('status', '').lower() == 'activo']
    print(f"👥 Empleados activos: {len(empleados_activos)} de {len(empleados)} totales")
    
    # Diccionario de liquidaciones por employee_id
    liq_dict = {liq.get('employee_id'): liq for liq in liquidaciones if liq.get('employee_id')}
    
    datos = []
    for emp in empleados_activos:  # 🔥 Solo procesar empleados activos
        emp_id = emp.get('id')
        liquidacion = liq_dict.get(emp_id, {})
        componentes = extraer_componentes_compensacion(liquidacion)
        detalle_liquidacion = extraer_detalle_liquidacion(liquidacion)
        
        # Calcular antigüedad
        antiguedad = 0
        if emp.get('active_since'):
            try:
                fecha_inicio = datetime.strptime(emp.get('active_since'), '%Y-%m-%d')
                antiguedad = round((datetime.now() - fecha_inicio).days / 365.25, 1)
            except:
                pass
        
        current_job = emp.get('current_job', {})
        boss = current_job.get('boss', {}) if current_job else {}
        
        # 🔥 OPTIMIZACIÓN 3: Obtener nombre del jefe usando el diccionario
        supervisor_nombre = None
        supervisor_id = boss.get('id')
        if supervisor_id and supervisor_id in empleados_dict:
            supervisor_nombre = empleados_dict[supervisor_id].get('full_name')
        
        registro = {
            # Identificación
            'ID_Empleado': emp_id,
            'RUT': emp.get('rut'),
            'Nombre_Completo': emp.get('full_name'),
            'Genero': emp.get('gender'),
            'Status': emp.get('status'),  # 🔥 Agregado para verificación
            'Antiguedad_Anos': antiguedad,
            
            # Información laboral
            'Cargo': current_job.get('role', {}).get('name') if current_job else None,
            'Area_ID': current_job.get('area_id') if current_job else None,
            'Supervisor_ID': supervisor_id,
            'Supervisor_RUT': boss.get('rut'),
            'Supervisor_Nombre': supervisor_nombre,  # 🔥 SOLUCIONADO: Nombre del jefe
            
            # Componentes de compensación (LO QUE PIDE MERCER)
            'Sueldo_Base': componentes['sueldo_base'],
            'Gratificacion': componentes['gratificacion'],
            'Asignaciones': componentes['asignaciones'],
            'Aguinaldos': componentes['aguinaldos'],
            'Bonos_Fijos': componentes['bonos_fijos'],
            'Bonos_Variables': componentes['bonos_variables'],
            'Comisiones': componentes['comisiones'],
            'Horas_Extras': componentes['horas_extras'],
            'Otros_Ingresos': componentes['otros_ingresos'],
            'Compensacion_Total': sum(componentes.values()),
            'Liquido_a_Pagar': liquidacion.get('liquid_reach', 0),
            'Tiene_Liquidacion': bool(liquidacion),
            
            # 💰 Nuevos campos: Ingresos principales
            'Income_Gross': detalle_liquidacion['income_gross'],
            'Income_Net': detalle_liquidacion['income_net'],
            'Income_AFP': detalle_liquidacion['income_afp'],
            'Income_IPS': detalle_liquidacion['income_ips'],
            'Total_Income_Taxable': detalle_liquidacion['total_income_taxable'],
            'Total_Income_NoTaxable': detalle_liquidacion['total_income_notaxable'],
            'Liquidacion_Closed': detalle_liquidacion['closed'],
            
            # 📉 Nuevos campos: Descuentos
            'Total_Legal_Discounts': detalle_liquidacion['total_legal_discounts'],
            'Total_Other_Discounts': detalle_liquidacion['total_other_discounts'],
            'Taxable_Base': detalle_liquidacion['taxable_base'],
            
            # 📋 Nuevos campos: Contadores de líneas
            'Total_Haberes': detalle_liquidacion['total_haberes'],
            'Total_Descuentos': detalle_liquidacion['total_descuentos'],
            'Total_Aportes': detalle_liquidacion['total_aportes'],
            'Total_Informativos': detalle_liquidacion['total_informativos'],
            
            # 💡 Nuevos campos: Detalle imponible vs no imponible
            'Haberes_Imponibles': detalle_liquidacion['haberes_imponibles'],
            'Haberes_No_Imponibles': detalle_liquidacion['haberes_no_imponibles'],
            'Descuentos_Legales': detalle_liquidacion['descuentos_legales'],
            'Descuentos_Voluntarios': detalle_liquidacion['descuentos_voluntarios']
        }
        datos.append(registro)
    
    df = pd.DataFrame(datos)
    
    # Generar Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = f"Reporte_Mercer_Activos_{timestamp}.xlsx"
    
    with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
        # 🔥 OPTIMIZACIÓN 4: Solo una hoja con empleados activos
        df.to_excel(writer, sheet_name='Empleados_Activos', index=False)
        
        # Hoja adicional con estadísticas
        stats = {
            'Métrica': [
                'Total Empleados Activos',
                'Con Liquidación',
                'Sin Liquidación', 
                'Con Gratificación',
                'Con Supervisor Identificado',
                'Compensación Total Promedio'
            ],
            'Valor': [
                len(df),
                len(df[df['Tiene_Liquidacion'] == True]),
                len(df[df['Tiene_Liquidacion'] == False]),
                len(df[df['Gratificacion'] > 0]),
                len(df[df['Supervisor_Nombre'].notna()]),
                f"${df['Compensacion_Total'].mean():,.0f}" if len(df) > 0 else 0
            ]
        }
        pd.DataFrame(stats).to_excel(writer, sheet_name='Estadisticas', index=False)
    
    print(f"✅ Archivo generado: {archivo}")
    print(f"📊 Empleados activos procesados: {len(df)}")
    print(f"💼 Con liquidación: {len(df[df['Tiene_Liquidacion'] == True])}")
    print(f"👨‍💼 Con supervisor identificado: {len(df[df['Supervisor_Nombre'].notna()])}")
    print(f"🎁 Con gratificación: {len(df[df['Gratificacion'] > 0])}")
    
    return archivo, df

# Función principal
def main():
    empleados = obtener_todos_los_empleados()
    liquidaciones = obtener_liquidaciones("30-08-2025")  # Fecha que funciona
    archivo, df = generar_excel_mercer(empleados, liquidaciones)
    return archivo, df

# Para ejecutar
if __name__ == "__main__":
    archivo_excel, dataframe = main()