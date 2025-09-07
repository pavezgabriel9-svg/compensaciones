#-----------------------------------------------------------
#                CompensaViewer v3.1 - Dashboard de Compensaciones
#                      VERSION CORREGIDA PARA NUEVA BD
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import traceback

# ----------------------------------------------------------
# Config BD
# ----------------------------------------------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "conexion_buk"


class CompensaViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        self.data_df = None
        self.employees_df = None
        self.setup_ui()
        # Primero verificamos la estructura de la BD
        self.verificar_estructura_bd()
        self.cargar_datos()

    def _configurar_ventana(self):
        self.root.title("Dashboard de Compensaciones")
        self.root.minsize(1300, 750)
        self.root.geometry("1350x800+50+50")
        self.root.configure(bg='#ecf0f1')

    # ------------------------------------------------------
    # Conexion BD con validaciones mejoradas
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

    def verificar_estructura_bd(self):
        """Verifica qué columnas existen en las tablas principales"""
        conn = self.conectar_bd()
        if not conn:
            return
        
        try:
            # Verificar columnas de historical_settlements
            cursor = conn.cursor()
            cursor.execute("DESCRIBE historical_settlements")
            columns_hs = [row[0] for row in cursor.fetchall()]
            
            print("Columnas en historical_settlements:", columns_hs)
            
            # Verificar columnas de employees
            cursor.execute("DESCRIBE employees")
            columns_emp = [row[0] for row in cursor.fetchall()]
            
            print("Columnas en employees:", columns_emp)
            
            # Verificar columnas de employees_jobs
            cursor.execute("DESCRIBE employees_jobs")
            columns_ej = [row[0] for row in cursor.fetchall()]
            
            print("Columnas en employees_jobs:", columns_ej)
            
            # Verificar columnas de areas
            cursor.execute("DESCRIBE areas")
            columns_areas = [row[0] for row in cursor.fetchall()]
            
            print("Columnas en areas:", columns_areas)
            
            conn.close()
            
        except Exception as e:
            print(f"Error verificando estructura: {e}")
            if conn:
                conn.close()

    def obtener_datos(self):
        """Obtiene datos históricos con query adaptada a la estructura real"""
        conn = self.conectar_bd()
        if not conn:
            return pd.DataFrame()
        
        try:
            # Query simplificada y adaptada
            query = """
            SELECT 
                -- Employees básicos
                e.person_id AS ID_Persona,
                e.rut AS RUT,
                e.full_name AS Nombre,
                COALESCE(e.gender, 'N/A') AS Género,
                e.active_since,
                e.birthday,
                e.area_id AS ID_Area_Actual,
                COALESCE(e.contract_type, 'N/A') AS Tipo_Contrato_Actual,
                
                -- Employees Jobs si existe
                COALESCE(ej.role_name, 'N/A') AS Cargo_Actual,
                COALESCE(e.name_role, 'N/A') AS Familia_Rol_Actual,
                ej.start_date,
                ej.end_date,
                ej.base_wage AS Sueldo_Base_Teorico,
                ej.boss_rut,
                
                -- Historical Settlements (adaptado)
                hs.periodo AS Período,
                YEAR(STR_TO_DATE(hs.periodo, '%m-%Y')) AS Año,
                MONTH(STR_TO_DATE(hs.periodo, '%m-%Y')) AS Mes,
                COALESCE(hs.ingreso_bruto, 0) AS Ingreso_Neto,
                COALESCE(hs.liquido_a_pagar, 0) AS Sueldo_Base_Liquidacion,
                COALESCE(hs.dias_trabajados, 0) AS Dias_Trabajados,
                COALESCE(hs.dias_no_trabajados, 0) AS Dias_No_Trabajados,
                
                -- Areas
                COALESCE(a.name, CONCAT('Área ', e.area_id)) AS Nombre_Area,
                a.first_level_name,
                a.second_level_name,
                a.cost_center,
                
                -- Datos del jefe
                COALESCE(jefe.full_name, 'Sin Asignar') AS Nombre_Jefe,
                jefe.rut AS RUT_Jefe

            FROM employees e
            LEFT JOIN employees_jobs ej
                ON e.rut = ej.person_rut
            LEFT JOIN historical_settlements hs
                ON e.rut = hs.rut
            LEFT JOIN areas a
                ON e.area_id = a.id
            LEFT JOIN employees jefe
                ON ej.boss_rut = jefe.rut
            ORDER BY e.person_id, hs.periodo
            """
            
            print("Ejecutando query...")
            df = pd.read_sql(query, conn)
            print(f"Query exitosa. Registros obtenidos: {len(df)}")

            # Post-procesamiento
            if not df.empty:
                # Calcular años de servicio
                df["Años_de_Servicio"] = (
                    pd.to_datetime("today").year - pd.to_datetime(df["active_since"], errors='coerce').dt.year
                ).fillna(0)

                # Crear columna Estado
                df["Estado"] = df["end_date"].apply(lambda x: "Activo" if pd.isna(x) else "Inactivo")

            conn.close()
            return df
        
        except Exception as e:
            print(f"Error completo: {traceback.format_exc()}")
            messagebox.showerror("Error SQL", f"Error consultando datos:\n{e}")
            if conn:
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
                person_id, full_name, rut, 
                COALESCE(email, '') as email,
                COALESCE(personal_email, '') as personal_email,
                COALESCE(address, '') as address,
                COALESCE(phone, '') as phone,
                gender, birthday, 
                COALESCE(university, '') as university,
                COALESCE(degree, '') as degree,
                COALESCE(bank, '') as bank,
                COALESCE(account_type, '') as account_type,
                COALESCE(account_number, '') as account_number,
                active_since, contract_type, area_id
            FROM employees
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo datos de empleados: {e}")
            if conn:
                conn.close()
            return pd.DataFrame()

    # ------------------------------------------------------
    # UI principal (sin cambios)
    # ------------------------------------------------------
    def setup_ui(self):
        # Título barra
        title_frame = tk.Frame(self.root, bg='#2980b9', height=60)
        title_frame.pack(fill='x')
        title_label = tk.Label(title_frame, text="📊 CompensaViewer v3.1 - Dashboard de Compensaciones",
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

        tk.Button(btn_frame, text="🔧 Verificar BD",
                  command=self.verificar_estructura_bd,
                  bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                  relief='flat', padx=20, pady=8).pack(side='left', padx=10)

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
    # Funciones principales (adaptadas)
    # ------------------------------------------------------
    def cargar_datos(self):
        print("Iniciando carga de datos...")
        self.data_df = self.obtener_datos()
        self.employees_df = self.obtener_datos_empleados()
        
        if self.data_df.empty:
            messagebox.showwarning("Sin datos", "No se encontraron datos en la base.")
            return

        print(f"Datos cargados: {len(self.data_df)} registros")

        # Poblar combos dinámicos
        periodos = sorted([p for p in self.data_df["Período"].dropna().unique() if p])
        areas = sorted([a for a in self.data_df["Nombre_Area"].dropna().unique() if a])
        
        self.periodo_combo['values'] = ["Todos"] + periodos
        self.area_combo['values'] = ["Todos"] + areas

        # Actualizar métricas
        self.actualizar_metricas()
        self.actualizar_tabla()

    def aplicar_filtros(self, df):
        if df.empty:
            return df
            
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
            mask_nombre = df["Nombre"].str.lower().apply(lambda x: all(p in x for p in palabras) if isinstance(x, str) else False)
            mask_rut = df["RUT"].astype(str).str.contains(search_term, case=False, na=False)
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
            self.total_emp_var.set("0")
            self.prom_teorico_var.set("$0")
            self.prom_liq_var.set("$0")
            self.prom_antiguedad_var.set("0 años")
            return

        # Usar solo último registro por persona para métricas
        df_ultimo = self.data_df.sort_values(["ID_Persona", "Año", "Mes"]).groupby("ID_Persona").tail(1)
        df_filtrado = self.aplicar_filtros(df_ultimo)

        if df_filtrado.empty:
            total = 0
            prom_teo = 0
            prom_liq = 0
            prom_antiguedad = 0
        else:
            total = len(df_filtrado)
            prom_teo = df_filtrado["Sueldo_Base_Teorico"].fillna(0).mean()
            prom_liq = df_filtrado["Sueldo_Base_Liquidacion"].fillna(0).mean()
            prom_antiguedad = df_filtrado["Años_de_Servicio"].fillna(0).mean()

        self.total_emp_var.set(str(total))
        self.prom_teorico_var.set(f"${prom_teo:,.0f}")
        self.prom_liq_var.set(f"${prom_liq:,.0f}")
        self.prom_antiguedad_var.set(f"{prom_antiguedad:.1f} años")

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
            sueldo_actual = f"${row['Sueldo_Base_Teorico']:,.0f}" if pd.notna(row['Sueldo_Base_Teorico']) and row['Sueldo_Base_Teorico'] > 0 else "N/A"
            jefatura = row.get('Nombre_Jefe', 'N/A') if pd.notna(row.get('Nombre_Jefe')) else "N/A"

            self.tree.insert("", "end", values=(
                row["RUT"], 
                row["Nombre"], 
                row["Cargo_Actual"],
                jefatura,
                sueldo_actual
            ))

    # ------------------------------------------------------
    # Funciones de ventanas secundarias (simplificadas por ahora)
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
        """Muestra ficha básica de la persona"""
        # Obtener datos de la persona
        df_persona = self.data_df[self.data_df["RUT"] == rut].copy()
        if df_persona.empty:
            messagebox.showwarning("Sin datos", f"No se encontraron datos para RUT: {rut}")
            return

        # Crear ventana simple
        win = tk.Toplevel(self.root)
        win.title(f"👤 Ficha de Persona - {df_persona['Nombre'].iloc[0]}")
        win.geometry("600x400+200+200")
        win.configure(bg='#f8f9fa')

        # Datos básicos
        ultimo = df_persona.sort_values(["Año", "Mes"]).iloc[-1]
        
        info_text = f"""
        INFORMACIÓN PERSONAL
        ═══════════════════
        RUT: {ultimo.get('RUT', 'N/A')}
        Nombre: {ultimo.get('Nombre', 'N/A')}
        Género: {ultimo.get('Género', 'N/A')}
        
        INFORMACIÓN LABORAL
        ════════════════════
        Cargo: {ultimo.get('Cargo_Actual', 'N/A')}
        Área: {ultimo.get('Nombre_Area', 'N/A')}
        Jefe: {ultimo.get('Nombre_Jefe', 'N/A')}
        Años de Servicio: {ultimo.get('Años_de_Servicio', 0):.1f} años
        Sueldo Base: ${ultimo.get('Sueldo_Base_Teorico', 0):,.0f}
        Estado: {ultimo.get('Estado', 'N/A')}
        
        HISTORIAL
        ═════════
        Total registros: {len(df_persona)}
        Último período: {ultimo.get('Período', 'N/A')}
        """
        
        text_widget = tk.Text(win, wrap=tk.WORD, font=('Consolas', 11))
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')
        
        tk.Button(win, text="Cerrar", command=win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11, 'bold')).pack(pady=10)

    def mostrar_evolucion(self):
        messagebox.showinfo("Función no implementada", "Esta función se implementará en una versión posterior.")

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
        columns = ('Área', 'Empleados', 'Sueldo Teórico Prom.')
        tree = ttk.Treeview(win, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200, anchor='center')

        # Calcular resumen por área
        resumen = df_ultimo.groupby('Nombre_Area').agg({
            'ID_Persona': 'nunique',
            'Sueldo_Base_Teorico': lambda x: x.fillna(0).mean()
        }).reset_index()

        # Llenar treeview
        for _, row in resumen.iterrows():
            tree.insert('', 'end', values=(
                row['Nombre_Area'],
                row['ID_Persona'],
                f"${row['Sueldo_Base_Teorico']:,.0f}"
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