#-----------------------------------------------------------
#                CompensaViewer v3.0 - Dashboard de Compensaciones
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ----------------------------------------------------------
# Config BD
# ----------------------------------------------------------
DB_HOST = "10.254.33.138"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

class CompensaViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self.data_df = None
        self.employees_df = None
        self.setup_ui()
        self.cargar_datos()

    def _configurar_ventana(self):
        self.root.title("📊 CompensaViewer v3.0 - Dashboard de Compensaciones")
        self.root.minsize(1300, 750)
        self.root.geometry("1350x800+50+50")
        self.root.configure(bg='#ecf0f1')

    # ------------------------------------------------------
    # Conexion BD
    # ------------------------------------------------------
    def conectar_bd(self):
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4"
            )
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo conectar:\n{e}")
            return None

    def obtener_datos(self):
        """Obtiene datos históricos con información de jefatura"""
        conn = self.conectar_bd()
        if not conn:
            return pd.DataFrame()
        
        try:
            # JOIN con employees para obtener datos del jefe
            query = """
            SELECT 
                hs.ID_Empleado, hs.ID_Persona, hs.RUT, hs.Nombre, hs.Género, 
                hs.Cargo_Actual, hs.Familia_Rol_Actual,
                hs.ID_Area_Actual, 
                COALESCE(a.name, CONCAT('Área ', hs.ID_Area_Actual)) as Nombre_Area,
                a.first_level_name, a.second_level_name, a.cost_center,
                hs.Tipo_Contrato_Actual,
                hs.Sueldo_Base_Teorico, hs.Sueldo_Base_Liquidacion,
                hs.Ingreso_Neto, hs.Años_de_Servicio, hs.Estado, hs.Período, hs.Año, hs.Mes,
                -- Datos del jefe
                jefe.full_name as Nombre_Jefe,
                jefe.rut_boss as RUT_Jefe
            FROM historical_settlements hs
            LEFT JOIN areas a ON hs.ID_Area_Actual = a.id
            LEFT JOIN employees jefe ON hs.RUT = jefe.rut
            ORDER BY hs.ID_Persona, hs.Año, hs.Mes
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            messagebox.showerror("Error SQL", f"Error consultando datos:\n{e}")
            conn.close()
            return pd.DataFrame()

    def obtener_datos_empleados(self):
        """Obtiene datos completos de empleados para la ficha"""
        conn = self.conectar_bd()
        if not conn:
            return pd.DataFrame()
        
        try:
            query = """
            SELECT 
                person_id, id, full_name, rut, email, personal_email,
                address, street, street_number, city, province, district, region, phone,
                gender, birthday, university, degree, bank, account_type, account_number,
                nationality, civil_status, health_company, pension_regime, pension_fund,
                active_since, status, start_date, end_date, contract_type,
                id_boss, rut_boss, base_wage, name_role, area_id, cost_center
            FROM employees
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo datos de empleados: {e}")
            conn.close()
            return pd.DataFrame()

    # ------------------------------------------------------
    # UI principal
    # ------------------------------------------------------
    def setup_ui(self):
        # Título barra
        title_frame = tk.Frame(self.root, bg='#2980b9', height=60)
        title_frame.pack(fill='x')
        title_label = tk.Label(title_frame, text="📊 CompensaViewer v3.0 - Dashboard de Compensaciones",
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
    # Funciones principales
    # ------------------------------------------------------
    def cargar_datos(self):
        self.data_df = self.obtener_datos()
        self.employees_df = self.obtener_datos_empleados()
        
        if self.data_df.empty:
            messagebox.showwarning("Sin datos", "No se encontraron datos en la base.")
            return

        # Poblar combos dinámicos
        periodos = sorted(self.data_df["Período"].dropna().unique())
        areas = sorted(self.data_df["Nombre_Area"].dropna().unique())
        
        self.periodo_combo['values'] = ["Todos"] + periodos
        self.area_combo['values'] = ["Todos"] + areas

        # Actualizar métricas
        self.actualizar_metricas()
        self.actualizar_tabla()

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
    # MEJORADO: Ficha de Persona con diseño compacto y profesional
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
        """MEJORADO: Muestra ficha completa de la persona con gráfico abajo y permite abrir varias fichas"""
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
        """MEJORADO: Pestaña compacta de datos + gráfico de evolución abajo"""
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

        # Información Personal (sin email personal, sin estado civil)
        card("📋 Información Personal", [
            ("RUT", ultimo.get('RUT', 'N/A')),
            ("Nombre", ultimo.get('Nombre', 'N/A')),
            ("Email Corporativo", (emp_info.get('email', 'N/A') if emp_info is not None else 'N/A')),
            ("Teléfono", (emp_info.get('phone', 'N/A') if emp_info is not None else 'N/A')),
            ("Género", ultimo.get('Género', 'N/A')),
            ("Fecha Nacimiento", (emp_info.get('birthday', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # Información Laboral (sin 'Estado', agregando Sueldo Base Actual)
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

        # Formación Académica (la conservamos)
        card("🎓 Formación Académica", [
            ("Universidad", (emp_info.get('university', 'N/A') if emp_info is not None else 'N/A')),
            ("Título/Grado", (emp_info.get('degree', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # Gráfico de evolución abajo
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