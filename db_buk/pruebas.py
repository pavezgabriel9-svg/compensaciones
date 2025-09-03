#-----------------------------------------------------------
#                CompensaViewer v3.0 - Demo Mejorado con Datos Simulados
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import random
import numpy as np

class CompensaViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self.data_df = None
        self.employees_df = None
        self.setup_ui()
        self.cargar_datos_simulados()

    def _configurar_ventana(self):
        self.root.title("📊 CompensaViewer v3.0 - Dashboard de Compensaciones (DEMO)")
        self.root.minsize(1300, 750)
        self.root.geometry("1350x800+50+50")
        self.root.configure(bg='#ecf0f1')

    # ------------------------------------------------------
    # Generación de datos simulados
    # ------------------------------------------------------
    def generar_datos_simulados(self):
        """Genera datos simulados realistas"""
        # Configuración base
        num_empleados = 150
        periodos = []
        
        # Generar periodos (últimos 24 meses)
        fecha_actual = datetime.now()
        for i in range(24):
            fecha = fecha_actual - timedelta(days=30*i)
            periodos.append(f"{fecha.year}-{fecha.month:02d}")
        
        periodos.reverse()
        
        # Áreas y configuraciones
        areas_config = {
            "Tecnología": {"empleados": 35, "sueldo_base": 1800000, "variacion": 0.3},
            "Ventas": {"empleados": 25, "sueldo_base": 1200000, "variacion": 0.4},
            "Marketing": {"empleados": 15, "sueldo_base": 1400000, "variacion": 0.25},
            "Recursos Humanos": {"empleados": 12, "sueldo_base": 1300000, "variacion": 0.2},
            "Finanzas": {"empleados": 18, "sueldo_base": 1600000, "variacion": 0.3},
            "Operaciones": {"empleados": 20, "sueldo_base": 1100000, "variacion": 0.35},
            "Legal": {"empleados": 8, "sueldo_base": 2000000, "variacion": 0.2},
            "Administración": {"empleados": 17, "sueldo_base": 900000, "variacion": 0.25}
        }
        
        cargos_por_area = {
            "Tecnología": ["Desarrollador Senior", "Desarrollador Junior", "Arquitecto de Software", "DevOps Engineer", "QA Analyst", "Tech Lead"],
            "Ventas": ["Ejecutivo de Ventas", "Gerente de Ventas", "Key Account Manager", "Inside Sales", "Sales Development Rep"],
            "Marketing": ["Marketing Manager", "Digital Marketing Specialist", "Content Creator", "Brand Manager", "Marketing Analyst"],
            "Recursos Humanos": ["HR Business Partner", "Recruiter", "HR Analyst", "Compensation Specialist", "Training Coordinator"],
            "Finanzas": ["Financial Analyst", "Controller", "Treasury Analyst", "Budget Analyst", "Accounts Payable"],
            "Operaciones": ["Operations Manager", "Process Analyst", "Supply Chain Coordinator", "Logistics Specialist"],
            "Legal": ["Legal Counsel", "Compliance Officer", "Contract Specialist"],
            "Administración": ["Administrative Assistant", "Office Manager", "Facilities Coordinator", "Executive Assistant"]
        }
        
        nombres = [
            "Ana García López", "Carlos Rodríguez Silva", "María González Pérez", "José Martínez Torres",
            "Laura Sánchez Ruiz", "Diego Fernández Castro", "Carmen López Morales", "Roberto Díaz Herrera",
            "Patricia Jiménez Ortega", "Manuel Ruiz Delgado", "Isabel Moreno Jiménez", "Francisco Álvarez Romero",
            "Elena Gutiérrez Navarro", "Antonio Hernández Vega", "Cristina Peña Molina", "Javier Castillo Ramos",
            "Mónica Vargas Iglesias", "Raúl Ortega Medina", "Silvia Ramos Guerrero", "Fernando Iglesias Cortés",
            "Beatriz Medina Flores", "Alejandro Guerrero Peña", "Natalia Cortés Aguilar", "Sergio Flores Mendoza",
            "Andrea Aguilar Campos", "Pablo Mendoza Vázquez", "Lucía Campos Herrero", "Adrián Vázquez Cabrera",
            "Verónica Herrero Gallego", "Iván Cabrera Prieto", "Alicia Gallego Santos", "Rubén Prieto Pascual",
            "Teresa Santos Domínguez", "Óscar Pascual Rubio", "Pilar Domínguez Marín", "Víctor Rubio Soto",
            "Nuria Marín Cano", "Gonzalo Soto Peña", "Rocío Cano Herrera", "Emilio Peña Morales",
            "Amparo Herrera Gil", "Ignacio Morales Ortiz", "Dolores Gil Serrano", "Ramón Ortiz Blanco",
            "Consuelo Serrano Muñoz", "Enrique Blanco Garrido", "Remedios Muñoz Calvo", "Tomás Garrido León",
            "Esperanza Calvo Hidalgo", "Alfredo León Márquez", "Milagros Hidalgo Vidal", "Esteban Márquez Mora",
            "Encarnación Vidal Lozano", "Nicolás Mora Peña", "Purificación Lozano Sanz", "Eugenio Peña Román",
            "Inmaculada Sanz Velasco", "Claudio Román Parra", "Concepción Velasco Bravo", "Aurelio Parra Méndez",
            "Asunción Bravo Herrero", "Leandro Méndez Fuentes", "Rosario Herrero Carrasco", "Cándido Fuentes Peña",
            "Soledad Carrasco Montero", "Plácido Peña Cabello", "Virtudes Montero Gallardo", "Benigno Cabello Mora",
            "Milagros Gallardo Vega", "Casimiro Mora Herrera", "Visitación Vega Serrano", "Demetrio Herrera Blanco",
            "Consolación Serrano Muñoz", "Evaristo Blanco Garrido", "Presentación Muñoz Calvo", "Florencio Garrido León",
            "Purificación Calvo Hidalgo", "Gumersindo León Márquez", "Encarnación Hidalgo Vidal", "Hermenegildo Márquez Mora",
            "Inmaculada Vidal Lozano", "Maximiliano Mora Peña", "Concepción Lozano Sanz", "Anacleto Peña Román",
            "Asunción Sanz Velasco", "Bartolomé Román Parra", "Rosario Velasco Bravo", "Crescencio Parra Méndez",
            "Soledad Bravo Herrero", "Delfín Méndez Fuentes", "Virtudes Herrero Carrasco", "Epifanio Fuentes Peña",
            "Milagros Carrasco Montero", "Fulgencio Peña Cabello", "Visitación Montero Gallardo", "Gaudencio Cabello Mora",
            "Consolación Gallardo Vega", "Hermógenes Mora Herrera", "Presentación Vega Serrano", "Inocencio Herrera Blanco",
            "Purificación Serrano Muñoz", "Jeremías Blanco Garrido", "Encarnación Muñoz Calvo", "Leoncio Garrido León",
            "Inmaculada Calvo Hidalgo", "Melquíades León Márquez", "Concepción Hidalgo Vidal", "Nemesio Márquez Mora",
            "Asunción Vidal Lozano", "Olegario Mora Peña", "Rosario Lozano Sanz", "Policarpo Peña Román",
            "Soledad Sanz Velasco", "Quintiliano Román Parra", "Virtudes Velasco Bravo", "Restituto Parra Méndez",
            "Milagros Bravo Herrero", "Saturnino Méndez Fuentes", "Visitación Herrero Carrasco", "Teófilo Fuentes Peña",
            "Consolación Carrasco Montero", "Urbano Peña Cabello", "Presentación Montero Gallardo", "Venancio Cabello Mora",
            "Purificación Gallardo Vega", "Wenceslao Mora Herrera", "Encarnación Vega Serrano", "Xerxes Herrera Blanco",
            "Inmaculada Serrano Muñoz", "Yago Blanco Garrido", "Concepción Muñoz Calvo", "Zacarías Garrido León"
        ]
        
        # Generar empleados base
        empleados = []
        id_persona = 1
        id_empleado = 1000
        
        for area, config in areas_config.items():
            for i in range(config["empleados"]):
                rut = f"{random.randint(10000000, 25000000)}-{random.choice('0123456789K')}"
                nombre = random.choice(nombres)
                # nombres.remove(nombre)  # Permitir duplicados para evitar IndexError
                
                empleado = {
                    "ID_Persona": id_persona,
                    "ID_Empleado": id_empleado,
                    "RUT": rut,
                    "Nombre": nombre,
                    "Género": random.choice(["Masculino", "Femenino"]),
                    "Cargo_Actual": random.choice(cargos_por_area[area]),
                    "Familia_Rol_Actual": f"Familia {area}",
                    "ID_Area_Actual": hash(area) % 100,
                    "Nombre_Area": area,
                    "first_level_name": f"División {area}",
                    "second_level_name": f"Subdivisión {area}",
                    "cost_center": f"CC{random.randint(1000, 9999)}",
                    "Tipo_Contrato_Actual": random.choice(["Indefinido", "Plazo Fijo", "Honorarios"]),
                    "sueldo_base": config["sueldo_base"],
                    "variacion": config["variacion"],
                    "anos_servicio_base": random.uniform(0.5, 15),
                    "Estado": random.choice(["Activo"] * 9 + ["Inactivo"])  # 90% activos
                }
                empleados.append(empleado)
                id_persona += 1
                id_empleado += 1
        
        # Generar datos históricos
        datos_historicos = []
        
        for empleado in empleados:
            anos_base = empleado["anos_servicio_base"]
            sueldo_base = empleado["sueldo_base"]
            variacion = empleado["variacion"]
            
            # Generar jefe (puede ser None)
            jefe_nombre = random.choice([None] + [e["Nombre"] for e in empleados[:20]])
            jefe_rut = None
            if jefe_nombre:
                jefe_empleado = next((e for e in empleados if e["Nombre"] == jefe_nombre), None)
                if jefe_empleado:
                    jefe_rut = jefe_empleado["RUT"]
            
            for i, periodo in enumerate(periodos):
                ano, mes = map(int, periodo.split('-'))
                
                # Calcular años de servicio progresivos
                anos_servicio = anos_base + (i * 30 / 365)  # Incremento mensual
                
                # Variación salarial realista (crecimiento + ruido)
                factor_crecimiento = 1 + (i * 0.003)  # 0.3% mensual aprox
                factor_ruido = random.uniform(1 - variacion/10, 1 + variacion/10)
                sueldo_teorico = int(sueldo_base * factor_crecimiento * factor_ruido)
                
                # Sueldo liquidación (generalmente menor)
                diferencia = random.uniform(0.02, 0.15)  # 2-15% menos
                sueldo_liquidacion = int(sueldo_teorico * (1 - diferencia))
                
                # Ingreso neto (aproximado)
                ingreso_neto = int(sueldo_liquidacion * random.uniform(0.75, 0.85))
                
                registro = {
                    "ID_Empleado": empleado["ID_Empleado"],
                    "ID_Persona": empleado["ID_Persona"],
                    "RUT": empleado["RUT"],
                    "Nombre": empleado["Nombre"],
                    "Género": empleado["Género"],
                    "Cargo_Actual": empleado["Cargo_Actual"],
                    "Familia_Rol_Actual": empleado["Familia_Rol_Actual"],
                    "ID_Area_Actual": empleado["ID_Area_Actual"],
                    "Nombre_Area": empleado["Nombre_Area"],
                    "first_level_name": empleado["first_level_name"],
                    "second_level_name": empleado["second_level_name"],
                    "cost_center": empleado["cost_center"],
                    "Tipo_Contrato_Actual": empleado["Tipo_Contrato_Actual"],
                    "Sueldo_Base_Teorico": sueldo_teorico,
                    "Sueldo_Base_Liquidacion": sueldo_liquidacion,
                    "Ingreso_Neto": ingreso_neto,
                    "Años_de_Servicio": round(anos_servicio, 1),
                    "Estado": empleado["Estado"],
                    "Período": periodo,
                    "Año": ano,
                    "Mes": mes,
                    "Nombre_Jefe": jefe_nombre,
                    "RUT_Jefe": jefe_rut
                }
                datos_historicos.append(registro)
        
        return pd.DataFrame(datos_historicos), self.generar_datos_empleados_completos(empleados)
    
    def generar_datos_empleados_completos(self, empleados_base):
        """Genera datos completos de empleados para la ficha"""
        empleados_completos = []
        
        dominios_email = ["empresa.com", "corporativo.cl", "company.org"]
        bancos = ["Banco de Chile", "BCI", "Santander", "Estado", "Falabella", "Scotiabank"]
        universidades = ["Universidad de Chile", "PUC", "USACH", "UDP", "UAI", "UNAB", "UDD"]
        ciudades = ["Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta", "Temuco"]
        regiones = ["Metropolitana", "Valparaíso", "Biobío", "Coquimbo", "Antofagasta", "Araucanía"]
        
        for emp in empleados_base:
            nombre_parts = emp["Nombre"].split()
            email_name = f"{nombre_parts[0].lower()}.{nombre_parts[1].lower()}"
            
            empleado_completo = {
                "person_id": emp["ID_Persona"],
                "id": emp["ID_Empleado"],
                "full_name": emp["Nombre"],
                "rut": emp["RUT"],
                "email": f"{email_name}@{random.choice(dominios_email)}",
                "personal_email": f"{email_name}{random.randint(1, 999)}@gmail.com",
                "address": f"Calle {random.choice(['Las Flores', 'Los Álamos', 'San Martín', 'O\'Higgins', 'Providencia'])}",
                "street": f"Calle {random.choice(['Las Flores', 'Los Álamos', 'San Martín'])}",
                "street_number": str(random.randint(100, 9999)),
                "city": random.choice(ciudades),
                "province": random.choice(ciudades),
                "district": f"Comuna {random.randint(1, 20)}",
                "region": random.choice(regiones),
                "phone": f"+569{random.randint(10000000, 99999999)}",
                "gender": emp["Género"],
                "birthday": f"{random.randint(1970, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "university": random.choice(universidades),
                "degree": random.choice(["Ingeniería Comercial", "Ingeniería Civil", "Psicología", "Derecho", "Administración", "Contador Auditor"]),
                "bank": random.choice(bancos),
                "account_type": random.choice(["Cuenta Corriente", "Cuenta Vista", "Cuenta de Ahorro"]),
                "account_number": str(random.randint(10000000, 99999999)),
                "nationality": "Chilena",
                "civil_status": random.choice(["Soltero", "Casado", "Divorciado", "Viudo"]),
                "health_company": random.choice(["Fonasa", "Isapre Banmédica", "Isapre Colmena", "Isapre Cruz Blanca", "Isapre Consalud"]),
                "pension_regime": "AFP",
                "pension_fund": random.choice(["AFP Capital", "AFP Cuprum", "AFP Habitat", "AFP Planvital", "AFP ProVida"]),
                "active_since": f"{random.randint(2010, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "status": emp["Estado"],
                "start_date": f"{random.randint(2010, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "end_date": None if emp["Estado"] == "Activo" else f"{random.randint(2023, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "contract_type": emp["Tipo_Contrato_Actual"],
                "id_boss": random.randint(1000, 1020) if random.random() > 0.3 else None,
                "rut_boss": emp.get("RUT_Jefe"),
                "base_wage": emp["sueldo_base"],
                "name_role": emp["Cargo_Actual"],
                "area_id": emp["ID_Area_Actual"],
                "cost_center": emp["cost_center"]
            }
            empleados_completos.append(empleado_completo)
        
        return pd.DataFrame(empleados_completos)

    # ------------------------------------------------------
    # Funciones adaptadas para datos simulados
    # ------------------------------------------------------
    def conectar_bd(self):
        """Simulación de conexión - no hace nada en modo demo"""
        return True

    def obtener_datos(self):
        """Retorna datos simulados"""
        return self.data_df

    def obtener_datos_empleados(self):
        """Retorna datos de empleados simulados"""
        return self.employees_df

    def cargar_datos_simulados(self):
        """Carga datos simulados en lugar de la BD"""
        print("🔄 Generando datos simulados...")
        self.data_df, self.employees_df = self.generar_datos_simulados()
        print(f"✅ Datos generados: {len(self.data_df)} registros históricos, {len(self.employees_df)} empleados")
        
        if self.data_df.empty:
            messagebox.showwarning("Sin datos", "No se pudieron generar datos simulados.")
            return

        # Poblar combos dinámicos
        periodos = sorted(self.data_df["Período"].dropna().unique())
        areas = sorted(self.data_df["Nombre_Area"].dropna().unique())
        
        self.periodo_combo['values'] = ["Todos"] + periodos
        self.area_combo['values'] = ["Todos"] + areas

        # Actualizar métricas
        self.actualizar_metricas()
        self.actualizar_tabla()

    def cargar_datos(self):
        """Función original adaptada para usar datos simulados"""
        self.cargar_datos_simulados()

    # ------------------------------------------------------
    # UI principal (sin cambios)
    # ------------------------------------------------------
    def setup_ui(self):
        # Título barra
        title_frame = tk.Frame(self.root, bg='#2980b9', height=60)
        title_frame.pack(fill='x')
        title_label = tk.Label(title_frame, text="📊 CompensaViewer v3.0 - Dashboard de Compensaciones (DEMO)",
                               font=('Arial', 17, 'bold'), fg='white', bg='#2980b9')
        title_label.pack(expand=True, pady=15)

        # Marco principal
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Sección métricas
        self.crear_seccion_metricas(main_frame)

        # Sección filtros + tabla
        self.crear_seccion_principal(main_frame)

        # Sección acciones
        self.crear_seccion_acciones(main_frame)

    # ------------------------------------------------------
    # Sección métricas
    # ------------------------------------------------------
    def crear_seccion_metricas(self, parent):
        metrics_frame = tk.LabelFrame(parent, text="📈 Indicadores Principales",
                                      font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                      padx=10, pady=10)
        metrics_frame.pack(fill='x', pady=(0, 8))

        row_metrics = tk.Frame(metrics_frame, bg='#ecf0f1')
        row_metrics.pack(fill='x')

        # Variables
        self.total_emp_var = tk.StringVar(value="0")
        self.prom_teorico_var = tk.StringVar(value="0")
        self.prom_liq_var = tk.StringVar(value="0")
        self.prom_antiguedad_var = tk.StringVar(value="0")

        self._crear_metrica(row_metrics, "👥 Total Empleados", self.total_emp_var, '#3498db')
        self._crear_metrica(row_metrics, "💰 Sueldo Teórico Prom.", self.prom_teorico_var, '#27ae60')
        self._crear_metrica(row_metrics, "💸 Sueldo Liquidación Prom.", self.prom_liq_var, '#f39c12')
        self._crear_metrica(row_metrics, "⏰ Antigüedad Prom.", self.prom_antiguedad_var, '#9b59b6')

    def _crear_metrica(self, parent, titulo, variable, color):
        box = tk.Frame(parent, bg=color, relief='raised', bd=2, width=150, height=80)
        box.pack(side='left', expand=True, fill='both', padx=5, pady=5)

        tk.Label(box, text=titulo, font=('Arial', 11, 'bold'), fg='white', bg=color).pack(pady=(10, 5))
        tk.Label(box, textvariable=variable, font=('Arial', 16, 'bold'), fg='white', bg=color).pack()

    # ------------------------------------------------------
    # Filtros + Tabla
    # ------------------------------------------------------
    def crear_seccion_principal(self, parent):
        main_split = tk.Frame(parent, bg='#ecf0f1')
        main_split.pack(fill='both', expand=True, pady=(5, 0))

        # Filtros
        filtros_frame = tk.LabelFrame(main_split, text="🔍 Filtros y Búsqueda",
                                      font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                      padx=8, pady=8)
        filtros_frame.pack(fill='x')

        # Primera fila de filtros
        fila1 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila1.pack(fill='x', pady=2)

        tk.Label(fila1, text="Período:", bg='#ecf0f1').pack(side='left', padx=5)
        self.periodo_var = tk.StringVar(value="Todos")
        self.periodo_combo = ttk.Combobox(fila1, textvariable=self.periodo_var, state="readonly", width=12)
        self.periodo_combo.pack(side='left', padx=5)

        tk.Label(fila1, text="Área:", bg='#ecf0f1').pack(side='left', padx=5)
        self.area_var = tk.StringVar(value="Todos")
        self.area_combo = ttk.Combobox(fila1, textvariable=self.area_var, state="readonly", width=20)
        self.area_combo.pack(side='left', padx=5)

        # Segunda fila - Búsqueda por nombre/RUT
        fila2 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila2.pack(fill='x', pady=5)

        tk.Label(fila2, text="🔎 Buscar (Nombre/RUT):", bg='#ecf0f1', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        self.search_name_var = tk.StringVar()
        self.search_name_entry = ttk.Entry(fila2, textvariable=self.search_name_var, width=30)
        self.search_name_entry.pack(side='left', padx=5)
        
        # Bind para búsqueda en tiempo real
        self.search_name_entry.bind('<KeyRelease>', lambda event: self.actualizar_tabla())

        tk.Button(fila2, text="🔍 Aplicar Filtros",
                  command=self.actualizar_tabla, bg='#27ae60', fg='white',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=10)

        tk.Button(fila2, text="🧹 Limpiar",
                  command=self.limpiar_filtros, bg='#95a5a6', fg='white',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        # Tabla
        tabla_frame = tk.Frame(main_split, bg='#ecf0f1')
        tabla_frame.pack(fill='both', expand=True, pady=(8, 0))

        # Frame para tabla y scrollbars
        tree_frame = tk.Frame(tabla_frame, bg='#ecf0f1')
        tree_frame.pack(fill='both', expand=True)

        # Columnas simplificadas para vista inicial
        cols = ("RUT", "Nombre", "Cargo", "Jefatura", "Sueldo Base Actual")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)

        # Configurar columnas
        anchos = [120, 200, 150, 150, 130]
        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=anchos[i])

        # Bind para doble clic
        self.tree.bind("<Double-1>", self.abrir_ficha_persona)

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar_h = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        # Pack
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')

    # ------------------------------------------------------
    # Sección Acciones
    # ------------------------------------------------------
    def crear_seccion_acciones(self, parent):
        acciones_frame = tk.LabelFrame(parent, text="🚀 Acciones",
                                       font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                       padx=10, pady=10)
        acciones_frame.pack(fill='x', pady=(8, 0))

        btn_frame = tk.Frame(acciones_frame, bg='#ecf0f1')
        btn_frame.pack()

        tk.Button(btn_frame, text="📈 Ver Evolución Salarial",
                  command=self.mostrar_evolucion,
                  bg='#8e44ad', fg='white', font=('Arial', 11, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='left', padx=10)

        tk.Button(btn_frame, text="📊 Resumen por Área",
                  command=self.mostrar_resumen_areas,
                  bg='#e67e22', fg='white', font=('Arial', 11, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='left', padx=10)

        tk.Button(btn_frame, text="📥 Exportar a Excel",
                  command=self.exportar_excel,
                  bg='#16a085', fg='white', font=('Arial', 11, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='left', padx=10)

    # ------------------------------------------------------
    # Funciones principales (resto del código sin cambios)
    # ------------------------------------------------------
    def aplicar_filtros(self, df):
        # Filtro por período
        if self.periodo_var.get() != "Todos":
            df = df[df["Período"] == self.periodo_var.get()]
        
        # Filtro por área
        if self.area_var.get() != "Todos":
            df = df[df["Nombre_Area"] == self.area_var.get()]
        
        # Búsqueda mejorada por palabras separadas en nombre + RUT
        search_term = self.search_name_var.get().strip()
        if search_term:
            palabras = search_term.lower().split()
            # Buscar en nombre (todas las palabras) O en RUT (contiene)
            mask_nombre = df["Nombre"].str.lower().apply(lambda x: all(p in x for p in palabras))
            mask_rut = df["RUT"].str.contains(search_term, case=False, na=False)
            df = df[mask_nombre | mask_rut]
        
        return df

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.periodo_var.set("Todos")
        self.area_var.set("Todos")
        self.search_name_var.set("")
        self.actualizar_tabla()

    def actualizar_metricas(self):
        if self.data_df.empty:
            return

        # Usar solo último registro por persona para métricas
        df_ultimo = self.data_df.sort_values(["ID_Persona", "Año", "Mes"]).groupby("ID_Persona").tail(1)
        df_filtrado = self.aplicar_filtros(df_ultimo)

        total = len(df_filtrado) if not df_filtrado.empty else 0
        prom_teo = round(df_filtrado["Sueldo_Base_Teorico"].mean(), 0) if not df_filtrado.empty else 0
        prom_liq = round(df_filtrado["Sueldo_Base_Liquidacion"].mean(), 0) if not df_filtrado.empty else 0
        prom_antiguedad = round(df_filtrado["Años_de_Servicio"].mean(), 1) if not df_filtrado.empty else 0

        self.total_emp_var.set(str(total))
        self.prom_teorico_var.set(f"${prom_teo:,.0f}")
        self.prom_liq_var.set(f"${prom_liq:,.0f}")
        self.prom_antiguedad_var.set(f"{prom_antiguedad} años")

    def actualizar_tabla(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.data_df.empty:
            return

        # Mostrar solo último registro por persona
        df_ultimo = self.data_df.sort_values(["ID_Persona", "Año", "Mes"]).groupby("ID_Persona").tail(1)
        df_filtrado = self.aplicar_filtros(df_ultimo)

        # Actualizar métricas con datos filtrados
        self.actualizar_metricas()

        # Llenar tabla con vista simplificada
        for _, row in df_filtrado.iterrows():
            sueldo_actual = f"${row['Sueldo_Base_Teorico']:,.0f}" if pd.notna(row['Sueldo_Base_Teorico']) else "N/A"
            jefatura = row.get('Nombre_Jefe', 'N/A') if pd.notna(row.get('Nombre_Jefe')) else "N/A"

            self.tree.insert("", "end", values=(
                row["RUT"], 
                row["Nombre"], 
                row["Cargo_Actual"],
                jefatura,
                sueldo_actual
            ))

    # ------------------------------------------------------
    # 🔹 MEJORADO: Ficha de Persona con diseño compacto y profesional
    # ------------------------------------------------------
    def abrir_ficha_persona(self, event):
        """Abre la ficha detallada de una persona al hacer doble clic"""
        item = self.tree.focus()
        if not item:
            return
        
        values = self.tree.item(item, "values")
        rut = values[0]  # RUT está en la primera columna
        self.mostrar_ficha_persona(rut)

    def mostrar_ficha_persona(self, rut):
        """🔹 MEJORADO: Muestra ficha completa de la persona con gráfico abajo y permite abrir varias fichas"""
        # Obtener datos históricos de la persona
        df_persona = self.data_df[self.data_df["RUT"] == rut].copy()
        if df_persona.empty:
            messagebox.showwarning("Sin datos", f"No se encontraron datos para RUT: {rut}")
            return

        # Obtener datos adicionales del empleado
        emp_data = self.employees_df[self.employees_df["rut"] == rut]
        emp_info = emp_data.iloc[0] if not emp_data.empty else None

        # Crear ventana de ficha (sin grab_set para permitir múltiples ventanas)
        win = tk.Toplevel(self.root)
        win.title(f"👤 Ficha de Persona - {df_persona['Nombre'].iloc[0]}")
        win.geometry("1200x800+100+50")
        win.configure(bg='#f8f9fa')
        # win.grab_set()  # ← Comentado para permitir múltiples fichas abiertas

        # Notebook
        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña Datos Generales (con gráfico abajo)
        self.crear_pestaña_datos_generales(notebook, df_persona, emp_info)

        # Pestaña Historial Completo
        self.crear_pestaña_historial(notebook, df_persona)

        # Seleccionar por defecto la pestaña de Datos Generales (índice 0) donde ya está el gráfico
        notebook.select(0)

    def crear_pestaña_datos_generales(self, notebook, df_persona, emp_info):
        """🔹 MEJORADO: Pestaña compacta de datos + gráfico de evolución abajo"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📋 Datos + Evolución")

        # Contenedor con scroll por si hay pantallas más pequeñas
        canvas = tk.Canvas(frame, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Último registro
        ultimo = df_persona.sort_values(["Año", "Mes"]).iloc[-1]

        # Encabezado
        header = tk.Frame(scrollable_frame, bg='#f8f9fa')
        header.pack(fill='x', pady=(5, 0))
        tk.Label(header, text=ultimo.get('Nombre', 'N/A'),
                 font=('Arial', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=8)
        tk.Label(header, text=f"RUT: {ultimo.get('RUT','N/A')}  •  Área: {ultimo.get('Nombre_Area','N/A')}  •  Cargo: {ultimo.get('Cargo_Actual','N/A')}",
                 font=('Arial', 10), bg='#f8f9fa', fg='#5d6d7e').pack(anchor='w', padx=8, pady=(2, 10))

        # Tarjetas (estilo limpio y profesional)
        cards = tk.Frame(scrollable_frame, bg='#f8f9fa')
        cards.pack(fill='x', padx=8)

        def card(title, rows):
            c = tk.LabelFrame(cards, text=title, font=('Arial', 11, 'bold'),
                              bg='white', fg='#2c3e50', padx=12, pady=10, labelanchor='n')
            c.pack(side='left', fill='both', expand=True, padx=6, pady=6)
            for i, (k, v) in enumerate(rows):
                tk.Label(c, text=f"{k}:", font=('Arial', 10, 'bold'), bg='white', fg='#34495e').grid(row=i, column=0, sticky='w', pady=3, padx=(0, 8))
                tk.Label(c, text=str(v), font=('Arial', 10), bg='white', fg='#2c3e50').grid(row=i, column=1, sticky='w', pady=3)

        # 🔹 Información Personal (sin email personal, sin estado civil)
        card("📋 Información Personal", [
            ("RUT", ultimo.get('RUT', 'N/A')),
            ("Nombre", ultimo.get('Nombre', 'N/A')),
            ("Email Corporativo", (emp_info.get('email', 'N/A') if emp_info is not None else 'N/A')),
            ("Teléfono", (emp_info.get('phone', 'N/A') if emp_info is not None else 'N/A')),
            ("Género", ultimo.get('Género', 'N/A')),
            ("Fecha Nacimiento", (emp_info.get('birthday', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # 🔹 Información Laboral (sin 'Estado', agregando Sueldo Base Actual)
        sueldo_actual = ultimo.get('Sueldo_Base_Teorico', None)
        sueldo_txt = f"${sueldo_actual:,.0f}" if pd.notna(sueldo_actual) else "N/A"
        card("💼 Información Laboral", [
            ("Cargo Actual", ultimo.get('Cargo_Actual', 'N/A')),
            ("Familia Rol", ultimo.get('Familia_Rol_Actual', 'N/A')),
            ("Área", ultimo.get('Nombre_Area', 'N/A')),
            ("Jefe Directo", ultimo.get('Nombre_Jefe', 'N/A')),
            ("Tipo Contrato", ultimo.get('Tipo_Contrato_Actual', 'N/A')),
            ("Años de Servicio", f"{ultimo.get('Años_de_Servicio', 0):.1f} años"),
            ("Sueldo Base Actual", sueldo_txt),
        ])

        # 🔹 Formación Académica (la conservamos)
        card("🎓 Formación Académica", [
            ("Universidad", (emp_info.get('university', 'N/A') if emp_info is not None else 'N/A')),
            ("Título/Grado", (emp_info.get('degree', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # 🔹 Gráfico de evolución abajo
        section_chart = tk.LabelFrame(scrollable_frame, text="📈 Evolución Salarial",
                                      font=('Arial', 11, 'bold'), bg='white', fg='#2c3e50',
                                      padx=10, pady=10, labelanchor='n')
        section_chart.pack(fill='both', expand=True, padx=8, pady=(6, 10))

        df_sueldo = df_persona.dropna(subset=["Sueldo_Base_Teorico"]).sort_values(["Año", "Mes"])
        if df_sueldo.empty:
            tk.Label(section_chart, text="No hay datos de sueldo base para mostrar",
                     font=('Arial', 10), bg='white', fg='#7f8c8d').pack(pady=30)
        else:
            fig, ax = plt.subplots(figsize=(10, 4.8))
            ax.plot(df_sueldo["Período"], df_sueldo["Sueldo_Base_Teorico"],
                    marker='o', linewidth=2, label="Sueldo Base Teórico", color='#3498db', markersize=5)
            if not df_sueldo["Sueldo_Base_Liquidacion"].isna().all():
                ax.plot(df_sueldo["Período"], df_sueldo["Sueldo_Base_Liquidacion"],
                        marker='s', linewidth=2, label="Sueldo Base Liquidación", color='#e74c3c', markersize=5)
            ax.legend(fontsize=9)
            ax.set_xlabel("Período", fontsize=10)
            ax.set_ylabel("Sueldo ($)", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            plt.tight_layout()

            canvas_chart = FigureCanvasTkAgg(fig, master=section_chart)
            canvas_chart.draw()
            canvas_chart.get_tk_widget().pack(fill='both', expand=True)

            # Stats compactas
            primer = df_sueldo["Sueldo_Base_Teorico"].iloc[0]
            ultimo_val = df_sueldo["Sueldo_Base_Teorico"].iloc[-1]
            variacion = ultimo_val - primer
            var_pct = (ultimo_val / primer - 1) * 100 if primer > 0 else 0
            tk.Label(section_chart,
                     text=f"Primer: ${primer:,.0f} | Último: ${ultimo_val:,.0f} | Variación: ${variacion:,.0f} ({var_pct:+.1f}%)",
                     font=('Arial', 10, 'bold'), bg='white', fg='#2c3e50').pack(pady=(6, 0))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def crear_pestaña_historial(self, notebook, df_persona):
        """Crea la pestaña de historial completo"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📜 Historial Completo")

        # Título
        tk.Label(frame, text=f"📜 Historial Completo - {df_persona['Nombre'].iloc[0]}", 
                font=('Arial', 14, 'bold')).pack(pady=10)

        # Crear treeview para historial
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        cols = ("Período", "Cargo", "Área", "Sueldo Teórico", "Sueldo Liquidación", 
                "Ingreso Neto", "Años Servicio", "Estado")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)

        # Configurar columnas
        anchos = [80, 120, 120, 120, 120, 120, 100, 80]
        for i, col in enumerate(cols):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=anchos[i])

        # Llenar con datos históricos
        df_ordenado = df_persona.sort_values(["Año", "Mes"], ascending=False)
        for _, row in df_ordenado.iterrows():
            sueldo_teo = f"${row['Sueldo_Base_Teorico']:,.0f}" if pd.notna(row['Sueldo_Base_Teorico']) else "N/A"
            sueldo_liq = f"${row['Sueldo_Base_Liquidacion']:,.0f}" if pd.notna(row['Sueldo_Base_Liquidacion']) else "N/A"
            ingreso_neto = f"${row['Ingreso_Neto']:,.0f}" if pd.notna(row['Ingreso_Neto']) else "N/A"
            anos_servicio = f"{row['Años_de_Servicio']:.1f}" if pd.notna(row['Años_de_Servicio']) else "N/A"

            tree.insert("", "end", values=(
                row["Período"], row["Cargo_Actual"], row["Nombre_Area"],
                sueldo_teo, sueldo_liq, ingreso_neto, anos_servicio, row["Estado"]
            ))

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        scrollbar_h = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')

    # ------------------------------------------------------
    # Funciones existentes (adaptadas)
    # ------------------------------------------------------
    def mostrar_evolucion(self):
        """Abre ventana de evolución salarial general"""
        if self.data_df.empty:
            messagebox.showwarning("Sin datos", "No hay información cargada.")
            return
        
        # Ventana secundaria
        win = tk.Toplevel(self.root)
        win.title("📈 Evolución Salarial General")
        win.geometry("1000x700+100+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()

        # Título
        tk.Label(win, text="📈 Análisis de Evolución Salarial General", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Frame de filtros
        filtros_frame = tk.LabelFrame(win, text="Seleccionar Análisis", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50',
                                     padx=15, pady=15)
        filtros_frame.pack(fill='x', padx=20, pady=10)

        # Filtro por área
        tk.Label(filtros_frame, text="🏢 Filtrar por Área:", bg='#f0f0f0', 
                font=('Arial', 11, 'bold')).pack(anchor='w', pady=5)
        area_var = tk.StringVar(value="")
        areas = sorted(self.data_df["Nombre_Area"].dropna().unique())
        area_combo = ttk.Combobox(filtros_frame, textvariable=area_var,
                                  values=areas, width=30)
        area_combo.pack(anchor='w', pady=5)

        # Frame para gráfico
        grafico_frame = tk.Frame(win, bg='#f0f0f0')
        grafico_frame.pack(fill='both', expand=True, padx=20, pady=10)

        def generar_grafico():
            # Limpiar frame anterior
            for widget in grafico_frame.winfo_children():
                widget.destroy()

            fig, ax = plt.subplots(figsize=(10, 5))
            df = self.data_df.copy()

            if area_var.get():
                # Análisis por área
                df = df[df["Nombre_Area"] == area_var.get()]
                if df.empty:
                    messagebox.showinfo("Info", "No hay datos para esa área.")
                    return

                df_grouped = df.groupby("Período").agg({
                    "Sueldo_Base_Teorico": "mean",
                    "Sueldo_Base_Liquidacion": "mean",
                    "ID_Empleado": "nunique"
                }).reset_index()

                ax.plot(df_grouped["Período"], df_grouped["Sueldo_Base_Teorico"], 
                       marker='o', linewidth=2, label="Sueldo Teórico Promedio", color='#27ae60')
                ax.plot(df_grouped["Período"], df_grouped["Sueldo_Base_Liquidacion"], 
                       marker='s', linewidth=2, label="Sueldo Liquidación Promedio", color='#f39c12')
                ax.set_title(f"Evolución Salarial Promedio - {area_var.get()}", fontsize=14, fontweight='bold')
            else:
                messagebox.showwarning("Filtro", "Selecciona un área.")
                return

            # Configurar gráfico
            ax.legend(fontsize=10)
            ax.set_xlabel("Período", fontsize=12)
            ax.set_ylabel("Sueldo ($)", fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

            plt.tight_layout()

            # Embebido en Tkinter
            canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

        # Botones
        btn_frame = tk.Frame(filtros_frame, bg='#f0f0f0')
        btn_frame.pack(fill='x', pady=10)

        tk.Button(btn_frame, text="📈 Generar Gráfico", 
                  command=generar_grafico, 
                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='left', padx=10)

        tk.Button(btn_frame, text="❌ Cerrar", 
                  command=win.destroy, 
                  bg='#95a5a6', fg='white', font=('Arial', 12, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='right', padx=10)

    def mostrar_resumen_areas(self):
        """Muestra resumen estadístico por áreas"""
        if self.data_df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para mostrar.")
            return

        # Usar solo último registro por persona
        df_ultimo = self.data_df.sort_values(["ID_Persona", "Año", "Mes"]).groupby("ID_Persona").tail(1)

        # Crear ventana de resumen
        win = tk.Toplevel(self.root)
        win.title("📊 Resumen por Área")
        win.geometry("800x600+200+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()

        tk.Label(win, text="📊 Resumen Estadístico por Área", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Crear treeview
        columns = ('Área', 'Empleados', 'Sueldo Teórico Prom.', 'Sueldo Liquidación Prom.', 'Diferencia Prom.')
        tree = ttk.Treeview(win, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')

        # Calcular resumen por área
        resumen = df_ultimo.groupby('Nombre_Area').agg({
            'ID_Persona': 'nunique',
            'Sueldo_Base_Teorico': 'mean',
            'Sueldo_Base_Liquidacion': 'mean'
        }).reset_index()

        resumen['Diferencia'] = resumen['Sueldo_Base_Teorico'] - resumen['Sueldo_Base_Liquidacion']

        # Llenar treeview
        for _, row in resumen.iterrows():
            tree.insert('', 'end', values=(
                row['Nombre_Area'],
                row['ID_Persona'],
                f"${row['Sueldo_Base_Teorico']:,.0f}",
                f"${row['Sueldo_Base_Liquidacion']:,.0f}",
                f"${row['Diferencia']:,.0f}"
            ))

        tree.pack(fill='both', expand=True, padx=20, pady=10)

        tk.Button(win, text="❌ Cerrar", command=win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(pady=15)

    def exportar_excel(self):
        """Exporta datos filtrados a Excel"""
        if self.data_df.empty:
            messagebox.showwarning("Sin datos", "No hay datos para exportar.")
            return

        try:
            df_export = self.aplicar_filtros(self.data_df)
            filename = f"compensaciones_export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            df_export.to_excel(filename, index=False)
            messagebox.showinfo("✅ Exportado", f"Datos exportados a: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando: {e}")

# ----------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CompensaViewer(root)
    root.mainloop()