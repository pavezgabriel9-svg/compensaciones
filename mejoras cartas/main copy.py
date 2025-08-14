
#importaciones
from docxtpl import DocxTemplate
from docx2pdf import convert
import pandas as pd
import os
import win32com.client as win32
from datetime import datetime
import re
import unidecode


# Obtener directorio del script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Rutas y configuración - USAR RUTAS ABSOLUTAS
TEMPLATES_DIR = os.path.join(script_dir, "Formatos Cartas")
TEMPLATE_DEFAULT = os.path.join(TEMPLATES_DIR, "carta_oferta_cramer.docx")
TEMPLATE_MAP = {
    "Lucerna 4925, Cerrillos, Santiago": os.path.join(TEMPLATES_DIR, "carta_oferta_cramer.docx"),
    "Las Encinas 268, Cerrillos, Santiago": os.path.join(TEMPLATES_DIR, "carta_oferta_syf.docx"),
    
}

# Ruta del CSV
CSV_PATH = r"C:\Users\gpavez\Desktop\Compensaciones\Cartas Oferta\info_candidatos(Hoja1).csv"
OUTPUT_FOLDER = "cartas_generadas"

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
    
    # Verificar plantilla por defecto
    if not os.path.exists(TEMPLATE_DEFAULT):
        plantillas_faltantes.append(TEMPLATE_DEFAULT)
    
    # Verificar todas las plantillas en el mapa
    for lugar, plantilla in TEMPLATE_MAP.items():
        if not os.path.exists(plantilla):
            plantillas_faltantes.append(plantilla)
    
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

# Buscar el archivo CSV
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
        
        # Eliminar puntos (separadores de miles) y reemplazar comas por puntos (separador decimal)
        valor_limpio = valor_str.replace('.', '')
        
        # Convertir a número entero
        valor_entero = int(float(valor_limpio))
        
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
    'correo_analista' 
    #'gratificacion', 'movilizacion', 'total_haberes', 'liquido_aproximado', 
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

# Procesar cada candidato
for index, row in df.iterrows():
    try:
        print(f"\nProcesando registro {index}: {row.get('nombre', 'Sin nombre')}")
        
        # Convertir la fila a dict
        row_dict = row.to_dict()
        
        # Verificar el estado del registro
        status = str(row_dict.get('status', '')).strip().lower()
        if 'status' in row_dict and status != 'pendiente':
            print(f"⏭️ Registro {index} omitido: estado '{status}' (no es 'pendiente')")
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

        # 1. Obtener dirección 
        lugar = row_dict.get('lugar_de_trabajo', VALORES_PREDETERMINADOS['lugar_de_trabajo'])
        
        # 2. Selecciono plantilla según el lugar
        template_path = TEMPLATE_MAP.get(lugar, TEMPLATE_DEFAULT)
        print(f"DEBUG: Usando plantilla '{template_path}' para lugar '{lugar}'")
        
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
        
        # Valores monetarios (mostrar antes y después del formateo)
        monetarios = [
            'sueldo_base', 'gratificacion', 'movilizacion', 'total_haberes', 
            'liquido_aproximado'
        ]

        for campo in monetarios:
            if campo in row_dict:
                valor_original = row_dict[campo]
                row_dict[campo] = formatear_valor_monetario(valor_original)
                print(f"DEBUG - Formato monetario: {campo} = {valor_original} -> {row_dict[campo]}")

        # Asegurar que tenemos la fecha actual
        row_dict['fecha'] = datetime.now().strftime("%d/%m/%Y")

        # 3. Cargo y renderizo con la plantilla escogida
        doc = DocxTemplate(template_path)
        print(f"DEBUG: Datos a renderizar = {row_dict}")
        doc.render(row_dict)

        # 4. Guardar documento
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