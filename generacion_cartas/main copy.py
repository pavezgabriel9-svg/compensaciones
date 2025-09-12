#importaciones
from docxtpl import DocxTemplate
from docx2pdf import convert
import pandas as pd
import os
import win32com.client as win32
from datetime import datetime
import re
import unidecode
import sys

# Obtener directorio del script actual
script_dir = os.path.dirname(os.path.abspath(__file__))

# Agregar el directorio actual al path
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Importar desde el mismo directorio
try:
    from calcular_liquido import calcular_liquido_desde_base, impuesto_unico
    print("✅ Funciones importadas correctamente")
except ImportError as e:
    print(f"❌ Error al importar funciones: {e}")
    print(f"Directorio actual: {script_dir}")
    print(f"Archivos en directorio actual: {os.listdir(script_dir)}")
    sys.exit(1)

# Rutas y configuración - USAR RUTAS ABSOLUTAS
TEMPLATES_DIR = os.path.join(script_dir, "Formatos Cartas")
TEMPLATE_DEFAULT = os.path.join(TEMPLATES_DIR, "carta_oferta_cramer.docx")

# Selección de plantillas
TEMPLATE_RULES = [
    
    # Cramer 
    {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_cramer.docx"),
        "criteria": {
            "lugar_de_trabajo": "Lucerna 4925; Cerrillos; Santiago",
            "bono": "Normal",
            "movilizacion": "Normal"
        }
    },
    {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_cramer_partnership.docx"),
        "criteria": {
            "lugar_de_trabajo": "Lucerna 4925; Cerrillos; Santiago",
            "bono": "Especialista Partnership",
            "movilizacion": "Normal"
        }
    },
    {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_cramer_kam.docx"),
        "criteria": {
            "lugar_de_trabajo": "Lucerna 4925; Cerrillos; Santiago",
            "bono": "KAM",
            "movilizacion": "Kam + asignación desgaste"
        }
    },

    # SyF
    {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_syf.docx"),
        "criteria": {
            "lugar_de_trabajo": "Las Encinas 268; Cerrillos; Santiago",
            "bono": "Normal",
            "movilizacion": "Normal"
        }
    },
     {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_syf_partnership.docx"),
        "criteria": {
            "lugar_de_trabajo": "Las Encinas 268; Cerrillos; Santiago",
            "bono": "Especialista Partnership",
            "movilizacion": "Normal"
        }
    },
    {
        "template": os.path.join(TEMPLATES_DIR, "carta_oferta_syf_kam.docx"),
        "criteria": {
            "lugar_de_trabajo": "Las Encinas 268; Cerrillos; Santiago",
            "bono": "KAM SyF",
            "movilizacion": "Kam + asignación desgaste"
        }
    },
]

# Ruta del CSV - Actualizar para buscar en el directorio del script
CSV_PATH = os.path.join(script_dir, "info_candidatos(Hoja1).csv")
OUTPUT_FOLDER = os.path.join(script_dir, "cartas_generadas")

# SOLUCIÓN 2: Verificar si el archivo existe antes de intentar leerlo
def encontrar_archivo_csv():
    """Busca el archivo CSV en diferentes ubicaciones posibles"""
    posibles_rutas = [
        "info_candidatos(Hoja1).csv",  # Directorio actual
        os.path.join(script_dir, "info_candidatos(Hoja1).csv"),  # Mismo directorio del script
        os.path.join(script_dir, "..", "info_candidatos(Hoja1).csv"),  # Directorio padre
        # Agrega más rutas si es necesario
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            print(f"✅ Archivo CSV encontrado en: {os.path.abspath(ruta)}")
            return ruta
    
    # Si no se encuentra, mostrar información de depuración
    print("❌ Archivo CSV no encontrado. Información de depuración:")
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Directorio del script: {script_dir}")
    print(f"Archivos en el directorio actual: {os.listdir('.')}")
    
    return None

# Función para verificar plantillas
def verificar_plantillas():
    """Verifica que todas las plantillas necesarias existan"""
    plantillas_faltantes = []
    
    # Verificar que existe el directorio de plantillas
    if not os.path.exists(TEMPLATES_DIR):
        print(f"❌ Directorio de plantillas no encontrado: {TEMPLATES_DIR}")
        return False
    
    # Verificar todas las plantillas en las reglas
    for rule in TEMPLATE_RULES:
        template_path = rule["template"]
        if not os.path.exists(template_path):
            plantillas_faltantes.append(template_path)
    
    if plantillas_faltantes:
        print("❌ Plantillas faltantes:")
        for p in set(plantillas_faltantes):  # usar set para evitar duplicados
            print(f"   - {p}")
        print(f"\nArchivos en el directorio de plantillas ({TEMPLATES_DIR}):")
        try:
            archivos = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.docx')]
            if archivos:
                for archivo in archivos:
                    print(f"   - {archivo}")
            else:
                print("   No se encontraron archivos .docx")
        except Exception as e:
            print(f"   Error al listar archivos: {e}")
        return False
    
    print("✅ Todas las plantillas encontradas correctamente")
    return True

# Crea carpeta
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Verificar plantillas antes de continuar
if not verificar_plantillas():
    print("\n⚠️ Por favor verifica que los archivos de plantilla estén en el directorio correcto:")
    print(f"   {script_dir}")
    exit(1)

# Buscar el archivo CSV usando la función de búsqueda
csv_encontrado = encontrar_archivo_csv()
if csv_encontrado:
    CSV_PATH = csv_encontrado
else:
    print(f"❌ No se pudo encontrar el archivo CSV en ninguna ubicación.")
    exit(1)

# Verificar que el archivo CSV existe
if not os.path.exists(CSV_PATH):
    print(f"❌ Archivo CSV no encontrado en: {CSV_PATH}")
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Directorio del script: {script_dir}")
    exit(1)

try:
    # Intentar con diferentes codificaciones
    encodings = ['utf-8',] #'latin-1', 'ISO-8859-1'
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(CSV_PATH, sep=';', encoding=encoding)
            print(f"✅ CSV leído correctamente con codificación: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    
    if df is None:
        raise Exception("No se pudo leer el archivo CSV con ninguna codificación.")
        
except Exception as e:
    print(f"✗ Error al leer el archivo CSV: {e}")
    exit(1)

# Imprimir columnas (depuración)
print(f"Columnas encontradas en el CSV: {df.columns.tolist()}")

# Verificar si existe la columna 'status'
if 'status' not in df.columns:
    print("⚠️ Advertencia: La columna 'status' no se encontró en el CSV. Se procesarán todos los registros.")

# Función para manejar valores monetarios directamente
def formatear_valor_monetario(valor):
    if pd.isna(valor) or valor == '':
        return "$ 0"
    try:
        # Convertir a string para manipulación
        valor_str = str(valor)
        
        # Eliminar cualquier símbolo de moneda existente
        valor_str = valor_str.replace('$', '').strip()
        
        # Si es un float, convertir primero a entero
        if '.' in valor_str and valor_str.replace('.', '').replace('-', '').isdigit():
            valor_entero = int(float(valor_str))
        else:
            # Eliminar puntos (separadores de miles) 
            valor_limpio = valor_str.replace('.', '').replace(',', '')
            valor_entero = int(valor_limpio)
        
        # Formatear con separador de miles usando punto
        return f"$ {valor_entero:,}".replace(",", ".")
    except Exception as e:
        print(f"Error al formatear valor monetario '{valor}': {e}")
        return "$ 0"

# quitar acentos para nombres de archivo
def normalizar_texto(texto):
    if not texto:
        return ""
    return unidecode.unidecode(str(texto))

# Función para crear nombres de archivo seguros
def crear_nombre_archivo_seguro(texto):
    if not texto:
        return "documento"
    # Normalizar y eliminar caracteres no deseados
    texto_normalizado = normalizar_texto(texto)
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', texto_normalizado)

# Función para evitar sobrescribir archivos
def obtener_nombre_disponible(base_path):
    if not os.path.exists(base_path):
        return base_path
    nombre_base, extension = os.path.splitext(base_path)
    contador = 1
    nuevo_path = f"{nombre_base} ({contador}){extension}"
    while os.path.exists(nuevo_path):
        contador += 1
        nuevo_path = f"{nombre_base} ({contador}){extension}"
    return nuevo_path

# Definir campos obligatorios para la carta
CAMPOS_OBLIGATORIOS = [
    'fecha_cierre', 'nombre', 'cargo', 'lugar_de_trabajo', 'jornada_de_trabajo', 
    'tipo_de_contrato', 'fecha_de_inicio', 'gerencia', 'sueldo_base', "bono","movilizacion",
    'correo_analista', "status"
]

# Valores predeterminados para campos que podrían faltar
VALORES_PREDETERMINADOS = {
    'lugar_de_trabajo': 'Oficina Central',
    'jornada_de_trabajo': 'Jornada Completa',
    'tipo_de_contrato': 'Plazo Fijo',  
    'fecha_de_inicio': 'Próxima semana',   
}

procesados = 0
omitidos = 0
ya_generados = 0

# función para seleccionar plantilla según reglas
def seleccionar_plantilla(row_dict):
    print(f"DEBUG - Criterios del registro:")
    print(f"  lugar_de_trabajo: '{row_dict.get('lugar_de_trabajo', '')}'")
    print(f"  bono: '{row_dict.get('bono', '')}'")
    print(f"  movilizacion: '{row_dict.get('movilizacion', '')}'")
    
    # 1. Buscar coincidencia exacta en reglas
    for i, rule in enumerate(TEMPLATE_RULES):
        print(f"\nDEBUG - Evaluando regla {i+1}: {os.path.basename(rule['template'])}")
        match = True
        for campo, valor in rule["criteria"].items():
            valor_registro = str(row_dict.get(campo, "")).strip()
            valor_criterio = str(valor).strip()
            print(f"  Comparando {campo}: '{valor_registro}' == '{valor_criterio}' -> {valor_registro == valor_criterio}")
            if valor_registro != valor_criterio:
                match = False
                break
        if match:
            print(f"✓ Plantilla seleccionada: {os.path.basename(rule['template'])}")
            return rule["template"]
    
    # 2. Fallback: usar plantilla por defecto
    print(f"⚠️ No se encontró plantilla específica para los criterios. Usando plantilla por defecto.")
    return TEMPLATE_DEFAULT

# Función para calcular sueldo base
def calcular_valores_automaticos(sueldo_base, tipo_movilizacion="Normal"):
    """
    Calcula gratificación, movilización, total_haberes y líquido_aproximado
    a partir del sueldo base usando Fonasa y AFP Uno
    tipo_movilizacion: "Normal" o "Kam + asignación desgaste"
    """
    try:
        # Convertir sueldo_base a número si viene como string
        if isinstance(sueldo_base, str):
            sueldo_base = float(sueldo_base.replace('$', '').replace('.', '').replace(',', ''))
        
        sueldo_base = float(sueldo_base)
        
        # Parámetros fijos
        ingreso_minimo = 529_000
        uf = 39_338
        tasa_afp = 0.1049
        tasa_fonasa = 0.07
        tasa_cesantia = 0.006
        
        # Calcular movilización y asignación de desgaste según tipo
        if tipo_movilizacion == "Kam + asignación desgaste":
            movilizacion_kam = 125_000  # Solo movilización KAM
            asignacion_desgaste = 250_000  # Asignación de desgaste separada
            movilizacion_total = movilizacion_kam + asignacion_desgaste  # Para cálculos internos
        else:  
            movilizacion_kam = 40_000  # Movilización normal
            asignacion_desgaste = 0  # Sin asignación de desgaste
            movilizacion_total = movilizacion_kam
        
        # Calcular gratificación legal
        tope_gratificacion_mensual = 4.75 * ingreso_minimo / 12
        gratificacion = min(0.25 * sueldo_base, tope_gratificacion_mensual)
        
        # Total imponible
        imponible = sueldo_base + gratificacion
        
        # Topes imponibles
        max_imponible_afp_salud = 87.8 * uf
        max_imponible_seguro_cesantia = 131.8 * uf
        
        # Descuentos
        cotiz_prev = min(imponible * tasa_afp, max_imponible_afp_salud * tasa_afp)
        cotiz_salud = min(imponible * tasa_fonasa, max_imponible_afp_salud * tasa_fonasa)
        cesantia = min(imponible * tasa_cesantia, max_imponible_seguro_cesantia * tasa_cesantia)
        
        # Base tributable e impuesto
        base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
        impuesto = impuesto_unico(base_tributable)
        
        # Cálculos finales
        total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto
        total_haberes = imponible + movilizacion_total
        liquido_aproximado = total_haberes - total_descuentos
        
        return {
            'gratificacion': gratificacion,
            'movilizacion': movilizacion_total,  # Para compatibilidad con plantillas normales
            'movilizacion_kam': movilizacion_kam,  # Para plantillas KAM
            'asignación_desgaste': asignacion_desgaste,  # Para plantillas KAM
            'total_haberes': total_haberes,
            'liquido_aproximado': liquido_aproximado
        }
        
    except Exception as e:
        print(f"Error en cálculo automático: {e}")
        # Aplicar movilización según tipo incluso en caso de error
        if tipo_movilizacion == "Kam + asignación desgaste":
            movilizacion_error = 375_000
            movilizacion_kam_error = 125_000
            asignacion_desgaste_error = 250_000
        else:
            movilizacion_error = 40_000
            movilizacion_kam_error = 40_000
            asignacion_desgaste_error = 0
            
        return {
            'gratificacion': 0,
            'movilizacion': movilizacion_error,
            'movilizacion_kam': movilizacion_kam_error,
            'asignación_desgaste': asignacion_desgaste_error,
            'total_haberes': sueldo_base + movilizacion_error,
            'liquido_aproximado': sueldo_base * 0.8  # Estimación conservadora
        }

# Procesar cada candidato
for index, row in df.iterrows():
    try:
        print(f"\nProcesando registro {index}: {row.get('nombre', 'Sin nombre')}")
        
        # Convertir la fila a dict
        row_dict = row.to_dict()
        
        # Verificar el estado del registro
        status = str(row_dict.get('status', '')).strip().lower()
        if 'status' in row_dict and status != 'pendiente':
            print(f" Registro {index} omitido: estado '{status}' (no es 'pendiente')")
            ya_generados += 1
            continue
        
        # Verificar que todos los campos obligatorios existan
        campos_faltantes = []
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in row_dict or pd.isna(row_dict[campo]) or row_dict[campo] == '':
                if campo in VALORES_PREDETERMINADOS:
                    row_dict[campo] = VALORES_PREDETERMINADOS[campo]
                    print(f"Aplicando valor predeterminado para {campo}: {VALORES_PREDETERMINADOS[campo]}")
                else:
                    campos_faltantes.append(campo)
        
        if campos_faltantes:
            print(f"⚠️ Registro {index} omitido: campos faltantes -> {', '.join(campos_faltantes)}")
            omitidos += 1
            continue
            
        nombre_raw = str(row_dict.get('nombre', '')).strip()

        # Validar nombre antes de cualquier procesamiento
        if not nombre_raw or not re.search(r'[a-zA-Z]', nombre_raw):
            print(f"⚠️ Registro {index} omitido: nombre inválido -> '{nombre_raw}'")
            omitidos += 1
            continue

        #Selección de plantilla ANTES de calcular valores (para preservar valores originales del CSV)
        template_path = seleccionar_plantilla(row_dict)

        # DESPUÉS calcular valores automáticamente desde sueldo_base
        sueldo_base = row_dict.get('sueldo_base', 0)
        tipo_movilizacion = row_dict.get('movilizacion', 'Normal')  # Obtener tipo de movilización del CSV
        valores_calculados = calcular_valores_automaticos(sueldo_base, tipo_movilizacion)
        
        # Agregar valores calculados al diccionario
        row_dict.update(valores_calculados)
        print(f"DEBUG - Valores calculados automáticamente (movilización: {tipo_movilizacion}):")
        for campo, valor in valores_calculados.items():
            print(f"  {campo}: {valor:,.0f}")

        print(f"DEBUG: Usando plantilla '{template_path}'")

        # Verificar que la plantilla existe
        if not os.path.exists(template_path):
            print(f"⚠️ Plantilla no encontrada: {template_path}")
            template_path = TEMPLATE_DEFAULT
            if not os.path.exists(template_path):
                print(f"✗ Plantilla por defecto tampoco encontrada: {template_path}")
                omitidos += 1
                continue
        
        nombre_archivo_base = f"Carta_{crear_nombre_archivo_seguro(nombre_raw)}.docx"

        # Mostrar datos originales para depuración
        print(f"DEBUG - tipo_de_contrato original: {row_dict.get('tipo_de_contrato', 'No disponible')}")
        print(f"DEBUG - fecha_de_inicio original: {row_dict.get('fecha_de_inicio', 'No disponible')}")
        
        # Valores monetarios (formatear los calculados y el sueldo base)
        monetarios = [
            'sueldo_base', 'gratificacion', 'movilizacion', 'movilizacion_kam', 
            'asignación_desgaste', 'total_haberes', 'liquido_aproximado'
        ]

        for campo in monetarios:
            if campo in row_dict:
                valor_original = row_dict[campo]
                row_dict[campo] = formatear_valor_monetario(valor_original)
                print(f"DEBUG - Formato monetario: {campo} = {valor_original} -> {row_dict[campo]}")

        # Asegurar que tenemos la fecha actual
        row_dict['fecha'] = datetime.now().strftime("%d/%m/%Y")

        # Cargo y renderizo con la plantilla escogida
        doc = DocxTemplate(template_path)
        print(f"DEBUG: Datos a renderizar = {row_dict}")
        doc.render(row_dict)

        # Guardar documento
        filepath = obtener_nombre_disponible(os.path.join(OUTPUT_FOLDER, nombre_archivo_base))
        doc.save(filepath)
        print(f"✓ Documento generado: {os.path.basename(filepath)}")

        # Convertir a PDF
        pdf_path = filepath.replace(".docx", ".pdf")
        try:
            convert(filepath, pdf_path)
            print(f"✓ PDF generado: {os.path.basename(pdf_path)}")
        except Exception as e:
            print(f"✗ Error al convertir a PDF: {e}")

        # Enviar por correo si está disponible el correo del analista
        correo_analista = row_dict.get("correo_analista", "")
        if correo_analista and "@" in correo_analista:
            try:
                outlook = win32.Dispatch('outlook.application')
                mail = outlook.CreateItem(0)
                mail.To = correo_analista
                mail.Subject = f"Oferta laboral para {nombre_raw}"
                mail.Body = f"""
Estimado/a,

Adjunto carta de oferta laboral para {nombre_raw}.

Saludos!!
"""
                mail.Attachments.Add(os.path.abspath(pdf_path))
                mail.Send()
                print(f"✓ Correo enviado a {correo_analista} con la carta de {nombre_raw}.")
            except Exception as e:
                print(f"✗ Error al enviar correo para {nombre_raw}: {e}")
        else:
            print(f"⚠️ No se envió correo para {nombre_raw}: dirección de correo inválida o no disponible.")

        procesados += 1

    except Exception as e:
        print(f"✗ Error procesando el registro {index}: {e}")
        omitidos += 1

print(f"\n✅ Proceso completado: {procesados} carta(s) generada(s). {omitidos} registro(s) omitido(s).")
print(f"📄 {ya_generados} registro(s) ya estaban marcados como generados y no se procesaron.")