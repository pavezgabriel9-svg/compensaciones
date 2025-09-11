# -----------------------------------------------------------
# Importaciones
# -----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import pymysql
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ----------------------------------------------------------
# Config BD
# ----------------------------------------------------------
# Config BD - Windows
# DB_HOST = "192.168.245.33"
# DB_USER = "compensaciones_rrhh"
# DB_PASSWORD = "_Cramercomp2025_"
# DB_NAME = "rrhh_app"

# Config BD - mac (ejemplo, comentado)
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
        self.settlements_df = None
        self.groups_df = None
        self.setup_ui() 
        self.cargar_datos()
        self._actualizar_tabla_grupos()  
        
    def _configurar_ventana(self):
        self.root.title("Dashboard de Compensaciones")
        self.root.minsize(1300, 750)
        self.root.configure(bg='#ecf0f1')

    def obtener_conexion(self):
        """Establece y retorna la conexión a la base de datos"""
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
        except pymysql.MySQLError as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {e}")
            return None

    def cargar_datos(self):
        """Carga los datos iniciales de todas las tablas necesarias."""
        conn = self.obtener_conexion()
        if conn:
            try:
                self.employees_df = pd.read_sql("SELECT * FROM employees", conn)
                self.settlements_df = pd.read_sql("SELECT * FROM historical_settlements", conn)
                self.groups_df = pd.read_sql("SELECT * FROM groups_table", conn)
                
                self.data_df = pd.merge(self.employees_df, self.settlements_df, on='rut', how='left')
                
                self.data_df['antiguedad_dias'] = (datetime.now() - pd.to_datetime(self.data_df['fecha_ingreso'])).dt.days
                self.actualizar_dashboard(self.data_df)
                # Añadir esta línea para actualizar la tabla de grupos
                self._actualizar_tabla_grupos()
                messagebox.showinfo("Datos Cargados", "Datos de empleados, liquidaciones y grupos cargados exitosamente.")
            except pymysql.MySQLError as e:
                messagebox.showerror("Error de Carga", f"No se pudieron cargar los datos: {e}")
            finally:
                conn.close()
        
    def actualizar_dashboard(self, df):
        """Actualiza todos los elementos del dashboard con los datos cargados"""
        if df is None or df.empty:
            messagebox.showwarning("Sin datos", "No se encontraron datos para mostrar en el dashboard.")
            return
            
        # Actualizar métricas
        self.actualizar_metricas()
        
        # Actualizar tabla
        self.actualizar_tabla()
        
        # Si tienes más elementos en el dashboard que necesiten actualizarse,
        # como gráficos o indicadores adicionales, actualízalos aquí

    # --- Funciones de Backend para Grupos ---
    def crear_grupo(self, nombre_grupo, descripcion):
        conn = self.obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                query = "INSERT INTO groups_table (group_name, group_description) VALUES (%s, %s)"
                cursor.execute(query, (nombre_grupo, descripcion))
                conn.commit()
                messagebox.showinfo("Éxito", f"Grupo '{nombre_grupo}' creado exitosamente.")
                
                # Actualizar el DataFrame de grupos después de crear uno nuevo
                self.groups_df = pd.read_sql("SELECT * FROM groups_table", conn)
                
                self._actualizar_tabla_grupos()
                return True
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"No se pudo crear el grupo: {e}")
                return False
            finally:
                conn.close()
    
    def agregar_empleado_a_grupo(self, group_id, rut_empleado):
        conn = self.obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                query = "INSERT INTO employees_group (group_id, rut) VALUES (%s, %s)"
                cursor.execute(query, (group_id, rut_empleado))
                conn.commit()
                return True
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"No se pudo agregar el empleado al grupo: {e}")
                return False
            finally:
                conn.close()

    def obtener_empleados_por_grupo(self, group_id):
        conn = self.obtener_conexion()
        if conn:
            try:
                query = """
                SELECT t1.*
                FROM employees AS t1
                JOIN employees_group AS t2 ON t1.rut = t2.rut
                WHERE t2.group_id = %s
                """
                return pd.read_sql(query, conn, params=(group_id,))
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"No se pudieron obtener los empleados del grupo: {e}")
                return pd.DataFrame()
            finally:
                conn.close()
        return pd.DataFrame()
        
    def eliminar_empleado_de_grupo(self, group_id, rut_empleado):
        conn = self.obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                query = "DELETE FROM employees_group WHERE group_id = %s AND rut = %s"
                cursor.execute(query, (group_id, rut_empleado))
                conn.commit()
                messagebox.showinfo("Éxito", "Empleado eliminado del grupo exitosamente.")
                self.cargar_datos()
                return True
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"No se pudo eliminar el empleado del grupo: {e}")
                return False
            finally:
                conn.close()

    def eliminar_grupo(self, group_id):
        conn = self.obtener_conexion()
        if conn:
            cursor = conn.cursor()
            try:
                query = "DELETE FROM groups_table WHERE group_id = %s"
                cursor.execute(query, (group_id,))
                conn.commit()
                messagebox.showinfo("Éxito", "Grupo eliminado exitosamente.")
                
                # Actualizar el DataFrame de grupos después de eliminar uno
                self.groups_df = pd.read_sql("SELECT * FROM groups_table", conn)
                
                self._actualizar_tabla_grupos()
                return True
            except pymysql.MySQLError as e:
                messagebox.showerror("Error", f"No se pudo eliminar el grupo: {e}")
                return False
            finally:
                conn.close()

    # --- Configuración de la UI ---
    def setup_ui(self):
        style = ttk.Style()
        style.configure("TNotebook", background='#ecf0f1')
        style.configure("TNotebook.Tab", padding=[15, 5])
        style.configure("TFrame", background='#ecf0f1')
        style.configure("TButton", font=('Arial', 10, 'bold'), relief='flat', background='#3498db', foreground='white')
        style.map("TButton", background=[('active', '#2980b9')])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Dashboard Tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self._setup_dashboard_ui()

        # Group Management Tab
        self.group_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.group_frame, text="Gestión de Grupos")
        self._setup_group_ui()

    def _setup_dashboard_ui(self):
        # Main Frame inside Dashboard tab
        main_frame = tk.Frame(self.dashboard_frame, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sección métricas
        self.crear_seccion_metricas(main_frame)
        
        # Sección filtros + tabla
        self.crear_seccion_principal(main_frame)

    def _setup_group_ui(self):
        # Frame para la creación de grupos
        creation_frame = ttk.Frame(self.group_frame, padding=10)
        creation_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(creation_frame, text="Crear Nuevo Grupo", font=('Arial', 12, 'bold')).pack(pady=5)
        
        ttk.Label(creation_frame, text="Nombre del Grupo:").pack(anchor='w', padx=5)
        self.group_name_entry = ttk.Entry(creation_frame, width=40)
        self.group_name_entry.pack(fill='x', padx=5)
        
        ttk.Label(creation_frame, text="Descripción:").pack(anchor='w', padx=5)
        self.group_desc_entry = ttk.Entry(creation_frame, width=40)
        self.group_desc_entry.pack(fill='x', padx=5)
        
        ttk.Button(creation_frame, text="Crear Grupo", command=self._crear_grupo_ui).pack(pady=10)

        # Frame para mostrar los grupos
        view_frame = ttk.Frame(self.group_frame, padding=10)
        view_frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(view_frame, text="Grupos Existentes", font=('Arial', 12, 'bold')).pack(pady=5)
        
        self.groups_tree = ttk.Treeview(view_frame, columns=('group_id', 'group_name'), show='headings')
        self.groups_tree.heading('group_id', text='ID')
        self.groups_tree.column('group_id', width=50, stretch=tk.NO)
        self.groups_tree.heading('group_name', text='Nombre del Grupo')
        self.groups_tree.column('group_name', width=250, stretch=tk.YES)
        self.groups_tree.pack(fill='both', expand=True)

        self.groups_tree.bind('<<TreeviewSelect>>', self._on_group_select)

        # Frame para botones de acción de grupo
        action_frame = ttk.Frame(view_frame)
        action_frame.pack(pady=5)
        ttk.Button(action_frame, text="❌ Eliminar Grupo", command=self._eliminar_grupo_ui).pack(side='left', padx=5)
        ttk.Button(action_frame, text="➕ Agregar/Eliminar Empleados", command=self._gestionar_empleados_grupo_ui).pack(side='left', padx=5)
        
        self._actualizar_tabla_grupos()

    def _crear_grupo_ui(self):
        """Función que maneja la creación de un grupo desde la UI."""
        nombre = self.group_name_entry.get()
        descripcion = self.group_desc_entry.get()
        if not nombre:
            messagebox.showwarning("Advertencia", "El nombre del grupo no puede estar vacío.")
            return
        self.crear_grupo(nombre, descripcion)
        self.group_name_entry.delete(0, tk.END)
        self.group_desc_entry.delete(0, tk.END)

    def _eliminar_grupo_ui(self):
        """Función que maneja la eliminación de un grupo desde la UI."""
        selected_item = self.groups_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un grupo para eliminar.")
            return
        group_id = self.groups_tree.item(selected_item, 'values')[0]
        if messagebox.askyesno("Confirmar Eliminación", "¿Estás seguro de que quieres eliminar este grupo?"):
            self.eliminar_grupo(group_id)

    def _on_group_select(self, event):
        """Maneja la selección de un grupo en la tabla."""
        selected_item = self.groups_tree.focus()
        if selected_item:
            # Obtiene el ID del grupo seleccionado
            self.selected_group_id = self.groups_tree.item(selected_item, 'values')[0]
        else:
            self.selected_group_id = None
    
    def _actualizar_tabla_grupos(self):
        """Actualiza la tabla de grupos con los datos de la base de datos."""
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
        if self.groups_df is not None and not self.groups_df.empty:
            for _, row in self.groups_df.iterrows():
                self.groups_tree.insert('', 'end', values=(row['group_id'], row['group_name']))

    def _gestionar_empleados_grupo_ui(self):
        """Abre una nueva ventana para gestionar los empleados de un grupo."""
        selected_item = self.groups_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un grupo para gestionar sus empleados.")
            return
        
        group_id = self.groups_tree.item(selected_item, 'values')[0]
        group_name = self.groups_tree.item(selected_item, 'values')[1]

        win = Toplevel(self.root)
        win.title(f"Gestión de Empleados para '{group_name}'")
        win.geometry("800x600")

        # Frame principal
        main_frame = ttk.Frame(win, padding=10)
        main_frame.pack(fill='both', expand=True)

        # Tablas de empleados
        empleados_frame = ttk.Frame(main_frame)
        empleados_frame.pack(fill='both', expand=True)

        # Tabla de todos los empleados
        ttk.Label(empleados_frame, text="Todos los Empleados", font=('Arial', 11, 'bold')).pack(pady=5)
        self.all_employees_tree = ttk.Treeview(empleados_frame, columns=('rut', 'nombre', 'cargo'), show='headings')
        self.all_employees_tree.heading('rut', text='RUT')
        self.all_employees_tree.heading('nombre', text='Nombre')
        self.all_employees_tree.heading('cargo', text='Cargo')
        self.all_employees_tree.pack(fill='both', expand=True, side='left', padx=5)

        # Tabla de empleados en el grupo
        ttk.Label(empleados_frame, text="Empleados en el Grupo", font=('Arial', 11, 'bold')).pack(pady=5)
        self.group_employees_tree = ttk.Treeview(empleados_frame, columns=('rut', 'nombre', 'cargo'), show='headings')
        self.group_employees_tree.heading('rut', text='RUT')
        self.group_employees_tree.heading('nombre', text='Nombre')
        self.group_employees_tree.heading('cargo', text='Cargo')
        self.group_employees_tree.pack(fill='both', expand=True, side='right', padx=5)
        
        # Botones de acción
        action_buttons_frame = ttk.Frame(win, padding=10)
        action_buttons_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(action_buttons_frame, text="➡ Agregar Seleccionado", command=lambda: self._agregar_empleado_a_grupo_ui(group_id)).pack(side='left', padx=5)
        ttk.Button(action_buttons_frame, text="⬅ Quitar Seleccionado", command=lambda: self._quitar_empleado_de_grupo_ui(group_id)).pack(side='right', padx=5)
        
        # Cargar datos en las tablas de la ventana emergente
        self._actualizar_tablas_gestion_empleados(group_id)

    def _actualizar_tablas_gestion_empleados(self, group_id):
        """Actualiza las tablas de gestión de empleados."""
        # Limpiar tablas
        for item in self.all_employees_tree.get_children():
            self.all_employees_tree.delete(item)
        for item in self.group_employees_tree.get_children():
            self.group_employees_tree.delete(item)

        # Obtener datos de empleados del grupo
        empleados_en_grupo = self.obtener_empleados_por_grupo(group_id)
        ruts_en_grupo = set(empleados_en_grupo['rut'])

        # Llenar la tabla de empleados en el grupo
        if not empleados_en_grupo.empty:
            for _, row in empleados_en_grupo.iterrows():
                self.group_employees_tree.insert('', 'end', values=(row['rut'], row['nombre_completo'], row['cargo']))

        # Llenar la tabla de todos los empleados (excluyendo los que ya están en el grupo)
        if self.employees_df is not None and not self.employees_df.empty:
            for _, row in self.employees_df.iterrows():
                if row['rut'] not in ruts_en_grupo:
                    self.all_employees_tree.insert('', 'end', values=(row['rut'], row['nombre_completo'], row['cargo']))

    def _agregar_empleado_a_grupo_ui(self, group_id):
        """Maneja la acción de agregar un empleado a un grupo desde la UI."""
        selected_item = self.all_employees_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un empleado de la lista de todos los empleados.")
            return
        rut_empleado = self.all_employees_tree.item(selected_item, 'values')[0]
        if self.agregar_empleado_a_grupo(group_id, rut_empleado):
            self._actualizar_tablas_gestion_empleados(group_id)

    def _quitar_empleado_de_grupo_ui(self, group_id):
        """Maneja la acción de quitar un empleado de un grupo desde la UI."""
        selected_item = self.group_employees_tree.focus()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un empleado del grupo para quitarlo.")
            return
        rut_empleado = self.group_employees_tree.item(selected_item, 'values')[0]
        if self.eliminar_empleado_de_grupo(group_id, rut_empleado):
            self._actualizar_tablas_gestion_empleados(group_id)
    
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
        """Obtiene datos con info de jefatura, cargo y sueldo desde employees_jobs"""
        conexion = self.conectar_bd()
        if not conexion:
            return pd.DataFrame()
        try:
            query = """
            SELECT
                e.person_id,
                e.rut,
                e.full_name AS Nombre,
                COALESCE(e.gender, 'N/A') AS Género,
                e.area_id AS ID_Area,
                COALESCE(e.contract_type, 'N/A') AS Tipo_Contrato,
                e.active_since,

                -- Historial desde employees_jobs
                ej.start_date,
                ej.end_date,
                ej.role_name AS Cargo_Actual,
                ej.base_wage AS Sueldo_Base,

                -- Área
                COALESCE(a.name, CONCAT('Área ', e.area_id)) AS Nombre_Area,

                -- Jefatura
                jefe.full_name AS Nombre_Jefe

            FROM employees_jobs ej
            JOIN employees e
                ON ej.person_rut = e.rut
            LEFT JOIN areas a
                ON e.area_id = a.id
            LEFT JOIN employees jefe
                ON ej.boss_rut = jefe.rut

            WHERE e.status = 'activo' AND ej.start_date >= '2018-01-01'
            ORDER BY e.full_name, ej.start_date;

            """
            df = pd.read_sql(query, conexion)
            if not df.empty:
                # Crear las columnas de fecha
                df['active_since'] = pd.to_datetime(df['active_since'], errors='coerce')
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')

                # Calcular Años_de_Servicio usando active_since (es la antigüedad del empleado)
                df["Años_de_Servicio"] = (pd.to_datetime("today").year - df["active_since"].dt.year).fillna(0)

                df['Período'] = df['start_date'].dt.to_period('M').astype(str)
                df['Año'] = df['start_date'].dt.year
                df['Mes'] = df['start_date'].dt.month

                df['sueldo_base'] = df['Sueldo_Base']
                
            conexion.close()
            return df
        except Exception as e:
            messagebox.showerror("Error SQL", f"Error consultando datos:\n{e}")
            try:
                conexion.close()
            except:
                pass
            return pd.DataFrame()
    
    
    def obtener_datos_empleados(self):
        """Obtiene datos completos de empleados para la ficha"""
        conn = self.conectar_bd()
        if not conn:
            return pd.DataFrame()
        try:
            query = """
            SELECT person_id, id, full_name, rut, email, phone, gender, birthday, 
            university, nationality, active_since, status, start_date, end_date, 
            contract_type, id_boss, rut_boss, base_wage, name_role, area_id, cost_center,
            degree
        
            FROM employees
            """
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error obteniendo datos de empleados: {e}")
            try:
                conn.close()
            except:
                pass
            return pd.DataFrame()
        
    def obtener_datos_liquidaciones(self):
        """Obtiene datos de liquidaciones desde historical_settlements."""
        conn = self.conectar_bd()
        if not conn:
            return pd.DataFrame()
        try:
            query = """
            SELECT
                `Pay_Period`,
                `RUT` AS rut,
                `Liquido_a_Pagar`
            FROM historical_settlements
            WHERE `Pay_Period` >= '2018-01-01'
            ORDER BY rut, `Pay_Period`;
            """
            df_liquidaciones = pd.read_sql(query, conn)
            if not df_liquidaciones.empty:
                df_liquidaciones['Pay_Period'] = pd.to_datetime(df_liquidaciones['Pay_Period'], errors='coerce')
                df_liquidaciones['Periodo_Liquidacion'] = df_liquidaciones['Pay_Period'].dt.to_period('M').astype(str)
                
                df_liquidaciones = df_liquidaciones.dropna(subset=['Pay_Period', 'rut', 'Liquido_a_Pagar'])

            conn.close()
            return df_liquidaciones
        except Exception as e:
            messagebox.showerror("Error SQL Liquidaciones", f"Error consultando datos de liquidaciones:\n{e}")
            try:
                conn.close()
            except:
                pass
            return pd.DataFrame()

    # ------------------------------------------------------
    # UI principal
    # ------------------------------------------------------
    # def setup_ui(self):
    #     # Configurar estilo del notebook
    #     style = ttk.Style()
    #     style.configure("TNotebook", background='#ecf0f1')
    #     style.configure("TNotebook.Tab", padding=[15, 5])
    #     style.configure("TFrame", background='#ecf0f1')
    #     style.configure("TButton", font=('Arial', 10, 'bold'), relief='flat', background='#3498db', foreground='white')
    #     style.map("TButton", background=[('active', '#2980b9')])

    #     # Título barra
    #     title_frame = tk.Frame(self.root, bg='#2980b9', height=60)
    #     title_frame.pack(fill='x')
    #     title_label = tk.Label(title_frame, text="Dashboard de Compensaciones", font=('Arial', 17, 'bold'), fg='white', bg='#2980b9')
    #     title_label.pack(expand=True, pady=15)

    #     # Crear el notebook
    #     self.notebook = ttk.Notebook(self.root)
    #     self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    #     # Dashboard Tab
    #     self.dashboard_frame = ttk.Frame(self.notebook)
    #     self.notebook.add(self.dashboard_frame, text="Dashboard")
        
    #     # Main Frame inside Dashboard tab
    #     main_frame = tk.Frame(self.dashboard_frame, bg='#ecf0f1')
    #     main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
    #     # Sección métricas
    #     self.crear_seccion_metricas(main_frame)
        
    #     # Sección filtros + tabla
    #     self.crear_seccion_principal(main_frame)

    #     # Group Management Tab
    #     self.group_frame = ttk.Frame(self.notebook)
    #     self.notebook.add(self.group_frame, text="Gestión de Grupos")
    #     self._setup_group_ui()

    # ------------------------------------------------------
    # Sección métricas
    # ------------------------------------------------------
    def crear_seccion_metricas(self, parent):
        metrics_frame = tk.LabelFrame(parent, text="Indicadores", font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=10, pady=10)
        metrics_frame.pack(fill='x', pady=(0, 8))
        row_metrics = tk.Frame(metrics_frame, bg='#ecf0f1')
        row_metrics.pack(fill='x')

        # Variables
        self.total_emp_var = tk.StringVar(value="0")
        self.prom_teorico_var = tk.StringVar(value="0")
        self.prom_liq_var = tk.StringVar(value="0")
        self.prom_antiguedad_var = tk.StringVar(value="0")

        self._crear_metrica(row_metrics, "Total Empleados", self.total_emp_var, '#3498db')
        self._crear_metrica(row_metrics, "Sueldo Base", self.prom_teorico_var, '#27ae60')
        self._crear_metrica(row_metrics, "Sueldo Líquido", self.prom_liq_var, '#f39c12')
        self._crear_metrica(row_metrics, "Antigüedad Promedio", self.prom_antiguedad_var, '#9b59b6')

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
        filtros_frame = tk.LabelFrame(main_split, text="Filtros y Búsqueda", font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=8, pady=8)
        filtros_frame.pack(fill='x')

        # Primera fila de filtros
        fila1 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila1.pack(fill='x', pady=2)
        
        #label período
        # tk.Label(fila1, text="Período:", bg='#ecf0f1').pack(side='left', padx=5)
        # self.periodo_var = tk.StringVar(value="Todos")
        # self.periodo_combo = ttk.Combobox(fila1, textvariable=self.periodo_var, state="readonly", width=12)
        # self.periodo_combo.pack(side='left', padx=5)
        
        #label área
        tk.Label(fila1, text="Área:", bg='#ecf0f1').pack(side='left', padx=5)
        self.area_var = tk.StringVar(value="Todos")
        self.area_combo = ttk.Combobox(fila1, textvariable=self.area_var, state="readonly", width=20)
        self.area_combo.pack(side='left', padx=5)
        
        #boton comparar
        self.btn_comparar = tk.Button(fila1, text="Comparar Seleccionados", command=self.comparar_seleccionados,
                                    state='disabled', bg='#2980b9', fg='white', font=('Arial', 10, 'bold'),
                                    relief='flat', padx=15, pady=5)
        self.btn_comparar.pack(side='right', padx=10)
                                                                                    
        # Segunda fila de filtros
        fila2 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila2.pack(fill='x', pady=5)
        
        # Búsqueda por nombre o rut
        tk.Label(fila2, text="Buscar por Nombre/rut:", bg='#ecf0f1').pack(side='left', padx=5)
        self.search_name_var = tk.StringVar()
        self.search_name_entry = ttk.Entry(fila2, textvariable=self.search_name_var, width=30)
        self.search_name_entry.pack(side='left', padx=5)
        self.search_name_entry.bind('<KeyRelease>', lambda event: self.actualizar_tabla())
        
        # Búsqueda por cargo
        tk.Label(fila2, text="Buscar por Cargo:", bg='#ecf0f1').pack(side='left', padx=10)
        self.search_cargo_var = tk.StringVar()
        self.search_cargo_entry = ttk.Entry(fila2, textvariable=self.search_cargo_var, width=20)
        self.search_cargo_entry.pack(side='left', padx=5)
        self.search_cargo_entry.bind('<KeyRelease>', lambda event: self.actualizar_tabla())
        
        # Búsqueda por Jefatura
        tk.Label(fila2, text="Buscar por Jefatura:", bg='#ecf0f1').pack(side='left', padx=10)
        self.search_jefatura_var = tk.StringVar()
        self.search_jefatura_entry = ttk.Entry(fila2, textvariable=self.search_jefatura_var, width=20)
        self.search_jefatura_entry.pack(side='left', padx=5)
        self.search_jefatura_entry.bind('<KeyRelease>', lambda event: self.actualizar_tabla())

        # botones filtrar y limpiar
        #tk.Button(fila2, text="Filtrar", command=self.actualizar_tabla, bg='#27ae60', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        tk.Button(fila2, text="Limpiar", command=self.limpiar_filtros, bg='#95a5a6', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=5)

        # Tabla
        tabla_frame = tk.Frame(main_split, bg='#ecf0f1')
        tabla_frame.pack(fill='both', expand=True, pady=(8, 0))

        # Frame para tabla y scrollbars
        tree_frame = tk.Frame(tabla_frame, bg='#ecf0f1')
        tree_frame.pack(fill='both', expand=True)

        # Columnas simplificadas para vista inicial
        cols = ("RUT", "Nombre", "Cargo", "Jefatura", "Sueldo Base", "Años de Servicio")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18, selectmode="extended")

        # Configurar columnas
        anchos = [50, 120, 200, 150, 150, 130]
        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=anchos[i])

        # Bind para doble clic
        self.tree.bind("<Double-1>", self.abrir_ficha_persona)
        self.tree.bind('<<TreeviewSelect>>', self.verificar_seleccion_para_comparar)

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
    # def crear_seccion_acciones(self, parent):
    #     acciones_frame = tk.LabelFrame(parent, text="Acciones", font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=10, pady=10)
    #     acciones_frame.pack(fill='x', pady=(8, 0))
    #     btn_frame = tk.Frame(acciones_frame, bg='#ecf0f1')
    #     btn_frame.pack()
    #     tk.Button(btn_frame, text="📈 Ver Evolución Salarial", command=self.mostrar_evolucion, bg='#8e44ad', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)
    #     tk.Button(btn_frame, text="📊 Resumen por Área", command=self.mostrar_resumen_areas, bg='#e67e22', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)
    #     tk.Button(btn_frame, text="📥 Exportar a Excel", command=self.exportar_excel, bg='#16a085', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)


    # ------------------------------------------------------
    # Funciones principales
    # ------------------------------------------------------
    def cargar_datos(self):
        self.data_df = self.obtener_datos()
        self.employees_df = self.obtener_datos_empleados()
        self.settlements_df = self.obtener_datos_liquidaciones()

        if self.data_df is None or self.data_df.empty:
            messagebox.showwarning("Sin datos", "No se encontraron datos en la base.")
            return

        # Poblar combos dinámicos
        #periodos = sorted(self.data_df["Período"].dropna().unique())
        areas = sorted(self.data_df["Nombre_Area"].dropna().unique())
        #self.periodo_combo['values'] = ["Todos"] + periodos
        self.area_combo['values'] = ["Todos"] + areas

        # Actualizar métricas y tabla
        self.actualizar_metricas()
        self.actualizar_tabla()

    def aplicar_filtros(self, df):
        # Filtro por período
        # if self.periodo_var.get() != "Todos":
        #     df = df[df["Período"] == self.periodo_var.get()]
        # Filtro por área
        if self.area_var.get() != "Todos":
            df = df[df["Nombre_Area"] == self.area_var.get()]
        # Búsqueda mejorada por palabras separadas en nombre + rut!!!!!
        search_term = self.search_name_var.get().strip()
        if search_term and not df.empty:
            palabras = search_term.lower().split()
            mask_nombre = df["Nombre"].str.lower().apply(lambda x: all(p in x for p in palabras) if isinstance(x, str) else False)
            mask_rut = df["rut"].str.contains(search_term, case=False, na=False)
            df = df[mask_nombre | mask_rut]
        # Búsqueda por Cargo
        search_cargo_term = self.search_cargo_var.get().strip()
        if search_cargo_term and not df.empty:
            df = df[df["Cargo_Actual"].str.contains(search_cargo_term, case=False, na=False)]
        # Búsqueda por Jefatura
        search_jefatura_term = self.search_jefatura_var.get().strip()
        if search_jefatura_term and not df.empty:
            df = df[df["Nombre_Jefe"].str.contains(search_jefatura_term, case=False, na=False)]
            
        return df
    

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        #self.periodo_var.set("Todos")
        self.area_var.set("Todos")
        self.search_name_var.set("")
        self.search_cargo_var.set("")
        self.search_jefatura_var.set("")
        self.actualizar_tabla()

    def comparar_grupos_seleccionados(self):
        """Compara todos los empleados de los grupos seleccionados."""
        selected_items = self.groups_tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Por favor, selecciona al menos un grupo para comparar.")
            return
        
        all_employees_to_compare = pd.DataFrame()
        for item in selected_items:
            group_id = self.groups_tree.item(item, 'values')[0]
            group_employees_df = self.obtener_empleados_por_grupo(group_id)
            all_employees_to_compare = pd.concat([all_employees_to_compare, group_employees_df])
            
        if all_employees_to_compare.empty:
            messagebox.showwarning("Sin Datos", "Los grupos seleccionados no contienen empleados para comparar.")
            return
            
        # Eliminar duplicados si un empleado está en varios grupos
        all_employees_to_compare.drop_duplicates(subset=['rut'], inplace=True)
        
        self.mostrar_comparacion_sueldos_generico(all_employees_to_compare)

    def mostrar_comparacion_sueldos_generico(self, df_a_comparar):
        """Muestra el gráfico de comparación de sueldos para un DataFrame dado."""
        win = Toplevel(self.root)
        win.title("Comparación de Sueldos")
        win.geometry("800x600")

        if df_a_comparar.empty:
            messagebox.showinfo("Sin datos", "No hay datos para comparar.")
            win.destroy()
            return
            
        # Merge con datos de liquidaciones
        comparacion_df = pd.merge(df_a_comparar, self.settlements_df, on='rut', how='left')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        for rut in comparacion_df['rut'].unique():
            df_rut = comparacion_df[comparacion_df['rut'] == rut].sort_values(by='periodo')
            nombre = df_rut['nombre_completo'].iloc[0] if not df_rut.empty else rut
            ax.plot(df_rut['periodo'], df_rut['sueldo_liquido'], marker='o', label=nombre)

        ax.set_title('Evolución de Sueldos Líquidos', fontsize=16)
        ax.set_xlabel('Período')
        ax.set_ylabel('Sueldo Líquido')
        ax.grid(True)
        ax.legend()
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Button(win, text="❌ Cerrar", command=win.destroy).pack(pady=10)



    def verificar_seleccion_para_comparar(self, event=None):
        """Habilita o deshabilita el botón de comparar según el número de elementos seleccionados."""
        seleccionados = self.tree.selection()
        if len(seleccionados) >= 2:
            self.btn_comparar.config(state='normal')
        else:
            self.btn_comparar.config(state='disabled')

    def comparar_seleccionados(self):
        """Recupera los RUTs de los empleados seleccionados y llama a la función de comparación."""
        seleccionados = self.tree.selection()
        if len(seleccionados) < 2:
            messagebox.showwarning("Selección mínima", "Por favor, selecciona al menos dos personas para comparar.")
            return
        ruts_a_comparar = []
        for item in seleccionados:
            valores_fila = self.tree.item(item, 'values')
            
        nombres_seleccionados = [self.tree.item(item, 'values')[0] for item in seleccionados]

        # Filtramos el DataFrame original para obtener los RUTs de los seleccionados
        df_filtrado_para_ruts = self.data_df[self.data_df['Nombre'].isin(nombres_seleccionados)].copy()

        #messagebox.showinfo("Prueba de Comparación", f"Empleados seleccionados para comparar:\n{nombres_seleccionados}")

    def comparar_seleccionados(self):
        """
        Recupera los RUTs de los empleados seleccionados y llama a la función de comparación.
        """
        seleccionados = self.tree.selection()
        if len(seleccionados) < 2:
            messagebox.showwarning("Selección mínima", "Por favor, selecciona al menos dos personas para comparar.")
            return

        ruts_a_comparar = []
        for item in seleccionados:
            rut = self.tree.item(item, "values")[0]
            ruts_a_comparar.append(rut)
            
        # Ahora llamamos a la función `mostrar_comparativa` que es un método de la clase
        self.mostrar_comparativa(ruts_a_comparar)


    def mostrar_comparativa(self, ruts):
        """
        Crea la ventana de comparación para los empleados con los RUTs proporcionados.
        """
        win = tk.Toplevel(self.root)
        win.title("Comparativa de Empleados")
        win.geometry("1400x800+50+50")
        win.configure(bg='#f8f9fa')
        
        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # --- Pestaña de Datos ---
        datos_frame = ttk.Frame(notebook)
        notebook.add(datos_frame, text="📋 Datos Comparativos")
        self.crear_pestaña_datos_comparativos(datos_frame, ruts)

        # --- Pestaña de Gráfico ---
        grafico_frame = ttk.Frame(notebook)
        notebook.add(grafico_frame, text="📈 Evolución Salarial Comparada")
        self.crear_pestaña_grafico_comparativo(grafico_frame, ruts)
        

    def crear_pestaña_datos_comparativos(self, parent_frame, ruts):
        """
        Genera la tabla de datos para la comparación.
        """
        # Usar un Treeview para una vista tabular de la información
        cols = ["Dato"] + [f"Empleado {i+1}" for i in range(len(ruts))]
        tree = ttk.Treeview(parent_frame, columns=cols, show="headings")
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor='w', width=150)

        # Obtener y preparar los datos de cada persona
        data_by_person = []
        for rut in ruts:
            # Aquí obtienes los datos de cada empleado, similar a como lo haces en abrir_ficha_persona
            # Usar el último registro disponible para la comparación
            df_persona_ultimo = self.data_df[self.data_df["rut"] == rut].sort_values('start_date').iloc[-1]
            
            # También puedes obtener datos adicionales del employees_df
            emp_info = self.employees_df[self.employees_df['rut'] == rut].iloc[0] if not self.employees_df[self.employees_df['rut'] == rut].empty else None
            
            # Unir los datos en un diccionario o estructura similar para fácil acceso
            person_data = {
                "Nombre": df_persona_ultimo['Nombre'],
                "RUT": df_persona_ultimo['rut'],
                "Cargo": df_persona_ultimo['Cargo_Actual'],
                "Área": df_persona_ultimo['Nombre_Area'],
                "Antigüedad (años)": f"{df_persona_ultimo['Años_de_Servicio']:.1f}",
                "Sueldo Base": f"${df_persona_ultimo['Sueldo_Base']:,.0f}",
                "Sueldo Líquido": "N/A", # Liquidaciones no están en data_df
                "Edad": "N/A" # Hay que calcular la edad desde el cumpleaños
            }
            
            # Recuperar sueldo líquido de settlements_df
            if self.settlements_df is not None:
                liq_df = self.settlements_df[self.settlements_df['rut'] == rut].sort_values('Pay_Period', ascending=False)
                if not liq_df.empty:
                    person_data["Sueldo Líquido"] = f"${liq_df['Liquido_a_Pagar'].iloc[0]:,.0f}"

            # Recuperar edad si el dato existe
            if emp_info is not None and pd.notna(emp_info.get('birthday')):
                edad = datetime.now().year - pd.to_datetime(emp_info['birthday']).year
                person_data["Edad"] = edad
            
            data_by_person.append(person_data)

        # Rellenar el Treeview con los datos comparativos
        if not data_by_person:
            tk.Label(parent_frame, text="No hay datos para comparar", font=('Arial', 12)).pack(pady=20)
            return

        # Usar el primer empleado como referencia para las filas
        referencia = data_by_person[0]
        for key in referencia:
            valores_fila = [key] + [d.get(key, 'N/A') for d in data_by_person]
            tree.insert("", "end", values=valores_fila)
            
        tree.pack(fill='both', expand=True, padx=10, pady=10)

    def crear_pestaña_grafico_comparativo(self, parent_frame, ruts):
        """
        Genera el gráfico comparativo de la evolución salarial.
        """
        fig, ax = plt.subplots(figsize=(10, 5))
        
        colores = plt.cm.get_cmap('tab10', len(ruts)) # Asignar un color único a cada persona
        
        for i, rut in enumerate(ruts):
            # Filtrar datos de sueldo base
            df_persona_base = self.data_df[self.data_df["rut"] == rut].copy()
            if df_persona_base.empty:
                continue
            
            # Preparar los datos de sueldo base para el gráfico (similar a la ficha de persona)
            df_persona_base.sort_values(by="start_date", inplace=True)
            df_persona_base['start_month'] = df_persona_base['start_date'].dt.to_period('M').dt.to_timestamp()
            
            # Obtener el último nombre para la leyenda
            nombre = df_persona_base.iloc[-1]['Nombre']
            
            # Trazar sueldo base
            ax.plot(df_persona_base['start_month'], df_persona_base['Sueldo_Base'], 
                    marker='o', linestyle='-', color=colores(i), label=f'{nombre} (Base)')
            
            # Trazar sueldo líquido si está disponible
            # df_liquidaciones_persona = self.settlements_df[self.settlements_df["rut"] == rut].copy()
            # if not df_liquidaciones_persona.empty:
            #     df_liquidaciones_persona.set_index('Pay_Period', inplace=True)
            #     ax.plot(df_liquidaciones_persona.index, df_liquidaciones_persona['Liquido_a_Pagar'], 
            #             marker='s', linestyle='--', color=colores(i), label=f'{nombre} (Líq.)')

        # Configuración del gráfico
        ax.legend(fontsize=8, loc='upper left')
        ax.set_xlabel("Período", fontsize=10)
        ax.set_ylabel("Sueldo ($)", fontsize=10)
        ax.set_title("Evolución Salarial Comparada", fontsize=12, pad=15)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.xticks(rotation=45)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        plt.tight_layout()
        
        # Embeber el gráfico en la ventana de Tkinter
        canvas_chart = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas_chart.draw()
        canvas_chart.get_tk_widget().pack(fill='both', expand=True)
        
        # Agregar una breve descripción de las métricas
        stats_text = "Se compara el Sueldo Base para cada empleado seleccionado."
        tk.Label(parent_frame, text=stats_text, font=('Arial', 10), bg='white', fg='#2c3e50').pack(pady=(6, 0))


    def actualizar_metricas(self):
        if self.data_df is None or self.data_df.empty:
            return
        df_ultimo = self.data_df.sort_values(["person_id", "Año", "Mes"]).groupby("person_id").tail(1)
        df_filtrado = self.aplicar_filtros(df_ultimo)
        total = len(df_filtrado) if not df_filtrado.empty else 0
        prom_teo = round(df_filtrado["Sueldo_Base"].mean(), 0) if not df_filtrado.empty else 0
        prom_liq = round(df_filtrado["sueldo_base"].mean(), 0) if not df_filtrado.empty else 0
        prom_antiguedad = round(df_filtrado["Años_de_Servicio"].mean(), 1) if not df_filtrado.empty else 0
        self.total_emp_var.set(str(total))
        self.prom_teorico_var.set(f"${prom_teo:,.0f}")
        self.prom_liq_var.set(f"${prom_liq:,.0f}")
        self.prom_antiguedad_var.set(f"{prom_antiguedad} años")

    def actualizar_tabla(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.data_df is None or self.data_df.empty:
            return
        # Mostrar solo último registro por persona
        df_ultimo = self.data_df.sort_values(["person_id", "Año", "Mes"]).groupby("person_id").tail(1)
        df_filtrado = self.aplicar_filtros(df_ultimo)
        self.actualizar_metricas()
        # Llenado de tabla
        for _, row in df_filtrado.iterrows():
            sueldo_actual = f"${row['Sueldo_Base']:,.0f}" if pd.notna(row.get('Sueldo_Base')) else "N/A"
            jefatura = row.get('Nombre_Jefe', 'N/A') if pd.notna(row.get('Nombre_Jefe')) else "N/A"
            cargo = row.get('Cargo_Actual', 'N/A')
            anos_servicio = f"{row.get('Años_de_Servicio', 0):.1f}"
            self.tree.insert("", "end", values=(
                row.get("rut", ""),
                row.get("Nombre", ""),
                cargo,
                jefatura,
                sueldo_actual,
                anos_servicio
            ))

    # ------------------------------------------------------
    # Ficha de Persona
    # ------------------------------------------------------
    def abrir_ficha_persona(self, event):
        """Abre la ficha detallada de una persona al hacer doble clic"""
        item = self.tree.focus()
        if not item:
            return
        values = self.tree.item(item, "values")
        if not values:
            return
        rut = values[0] 
        self.mostrar_ficha_persona(rut)

    def mostrar_ficha_persona(self, rut):
        """Muestra ficha completa de la persona con gráfico abajo"""
        if self.data_df is None or self.data_df.empty:
            messagebox.showwarning("Sin datos", "No hay datos cargados.")
            return

        # Obtener datos históricos de la persona (sueldo base por rol)
        df_persona_base = self.data_df[self.data_df["rut"] == rut].copy()
        if df_persona_base.empty:
            messagebox.showwarning("Sin datos", f"No se encontraron datos para rut: {rut}")
            return
        df_persona_base.sort_values(by="start_date", inplace=True)

        # Alinear las fechas de inicio al primer día del mes para el gráfico
        df_persona_base['start_month'] = df_persona_base['start_date'].dt.to_period('M').dt.to_timestamp()
        df_persona_base.set_index('start_month', inplace=True)
        
        # Obtener datos de liquidaciones
        df_liquidaciones_persona = pd.DataFrame()
        if self.settlements_df is not None and not self.settlements_df.empty:
            df_liquidaciones_persona = self.settlements_df[self.settlements_df["rut"] == rut].copy()
            if not df_liquidaciones_persona.empty:
                df_liquidaciones_persona.set_index('Pay_Period', inplace=True)

        active_since = df_persona_base['active_since'].min()
        start_date = active_since if pd.notna(active_since) else df_persona_base.index.min()
        
        end_date = datetime.now()
        df_completo = pd.DataFrame(index=pd.date_range(start=start_date, end=end_date, freq='MS'))
        
        # Unir los datos de sueldo base y líquido
        df_completo = df_completo.merge(df_persona_base[['Sueldo_Base']], left_index=True, right_index=True, how='left')
        df_completo = df_completo.merge(df_liquidaciones_persona[['Liquido_a_Pagar']], left_index=True, right_index=True, how='left')

        # Propagar el último valor conocido del sueldo base hacia adelante
        df_completo['Sueldo_Base'] = df_completo['Sueldo_Base'].ffill()

        # Restablecer el índice de fecha a una columna
        df_completo.reset_index(inplace=True)
        df_completo.rename(columns={'index': 'Fecha'}, inplace=True)
        df_completo['Año'] = df_completo['Fecha'].dt.year
        df_completo['Mes'] = df_completo['Fecha'].dt.month
        
        # Replicar los datos de la última fila para la tarjeta de información
        last_row_info = df_persona_base.iloc[-1].copy()
        for col in last_row_info.index:
            if col not in df_completo.columns:
                df_completo[col] = last_row_info[col]
        
        # Obtener datos adicionales del empleado
        emp_data = self.employees_df[self.employees_df["rut"] == rut] if (self.employees_df is not None) else pd.DataFrame()
        emp_info = emp_data.iloc[0] if not emp_data.empty else None

        # Crear ventana de ficha
        win = tk.Toplevel(self.root)
        win.title(f"Ficha de {df_completo['Nombre'].iloc[0]}")
        win.geometry("1200x800+100+50")
        win.configure(bg='#f8f9fa')

        # Notebook (pestañas)
        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña Datos Generales (con gráfico abajo)
        self.crear_pestaña_datos_generales(notebook, df_completo, emp_info)
        # Pestaña Historial Completo
        self.crear_pestaña_historial(notebook, df_completo)

        # Seleccionar la primera pestaña por defecto
        notebook.select(0)
    
    def crear_pestaña_datos_generales(self, notebook, df_persona, emp_info):
        """Pestaña compacta de datos + gráfico de evolución abajo"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Datos + Evolución")

        # Contenedor con scroll por si hay pantallas más pequeñas
        canvas = tk.Canvas(frame, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Último registro
        ultimo = df_persona.sort_values("Fecha").iloc[-1]

        # Encabezado
        header = tk.Frame(scrollable_frame, bg='#f8f9fa')
        header.pack(fill='x', pady=(5, 0))
        tk.Label(header, text=ultimo.get('Nombre', 'N/A'), font=('Arial', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=8)

        # Tarjetas
        cards = tk.Frame(scrollable_frame, bg='#f8f9fa')
        cards.pack(fill='x', padx=8)

        def card(title, rows):
            c = tk.LabelFrame(cards, text=title, font=('Arial', 11, 'bold'), bg='white', fg='#2c3e50', padx=12, pady=10, labelanchor='n')
            c.pack(side='left', fill='both', expand=True, padx=6, pady=6)
            for i, (k, v) in enumerate(rows):
                tk.Label(c, text=f"{k}:", font=('Arial', 10, 'bold'), bg='white', fg='#34495e').grid(row=i, column=0, sticky='w', pady=3, padx=(0, 8))
                tk.Label(c, text=str(v), font=('Arial', 10), bg='white', fg='#2c3e50').grid(row=i, column=1, sticky='w', pady=3)

        # Información Personal
        card("📋 Información Personal", [
            ("rut", ultimo.get('rut', 'N/A')),
            ("Nombre", ultimo.get('Nombre', 'N/A')),
            ("Email Corporativo", (emp_info.get('email', 'N/A') if emp_info is not None else 'N/A')),
            ("Género", ultimo.get('Género', 'N/A')),
            ("Fecha Nacimiento", (emp_info.get('birthday', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # Información Laboral
        sueldo_actual = ultimo.get('Sueldo_Base', None)
        sueldo_txt = f"${sueldo_actual:,.0f}" if pd.notna(sueldo_actual) else "N/A"
        sueldo_liquido_actual = ultimo.get('Liquido_a_Pagar', None)
        sueldo_liq_txt = f"${sueldo_liquido_actual:,.0f}" if pd.notna(sueldo_liquido_actual) else "N/A"

        card("💼 Información Laboral", [
            ("Cargo Actual", ultimo.get('Cargo_Actual', 'N/A')),
            ("Área", ultimo.get('Nombre_Area', 'N/A')),
            ("Jefe Directo", ultimo.get('Nombre_Jefe', 'N/A')),
            ("Tipo Contrato", ultimo.get('Tipo_Contrato', 'N/A')),
            ("Años de Servicio", f"{ultimo.get('Años_de_Servicio', 0):.1f} años"),
            ("Sueldo Base", sueldo_txt),
            ("Sueldo Líquido", sueldo_liq_txt),
        ])

        # Formación Académica
        card("🎓 Formación Académica", [
            ("Universidad", (emp_info.get('university', 'N/A') if emp_info is not None else 'N/A')),
            ("Título/Grado", (emp_info.get('degree', 'N/A') if emp_info is not None else 'N/A')),
        ])

        # Gráfico de evolución
        section_chart = tk.LabelFrame(scrollable_frame, text="Evolución Salarial", font=('Arial', 11, 'bold'), bg='white', fg='#2c3e50', padx=10, pady=10, labelanchor='n')
        section_chart.pack(fill='both', expand=True, padx=8, pady=(6, 10))
        
        df_sueldo_plot = df_persona.copy()

        if df_sueldo_plot.empty:
            tk.Label(section_chart, text="No hay datos de sueldo base para mostrar", font=('Arial', 10), bg='white', fg='#7f8c8d').pack(pady=30)
        else:
            fig, ax = plt.subplots(figsize=(10, 4.8))
            
            # El eje X ahora es la columna 'Fecha' que creaste al combinar los dataframes
            ax.plot(df_sueldo_plot["Fecha"], df_sueldo_plot["Sueldo_Base"], marker='o', linewidth=2, label="Sueldo Base")
            
            if "Liquido_a_Pagar" in df_sueldo_plot.columns and not df_sueldo_plot["Liquido_a_Pagar"].isna().all():
                # Asegúrate de que los valores líquidos se tracen en las fechas correctas
                ax.plot(df_sueldo_plot["Fecha"], df_sueldo_plot["Liquido_a_Pagar"], marker='s', linewidth=2, label="Sueldo Líquido")
            
            ax.legend(fontsize=9)
            ax.set_xlabel("Período", fontsize=10)
            ax.set_ylabel("Sueldo ($)", fontsize=10)
            ax.set_title(f"Evolución Salarial de {df_sueldo_plot.iloc[0].get('Nombre', 'N/A')}", fontsize=12, pad=15)

            # Ajusta el formateador de fechas para mostrar el año
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            plt.tight_layout()
            canvas_chart = FigureCanvasTkAgg(fig, master=section_chart)
            canvas_chart.draw()
            canvas_chart.get_tk_widget().pack(fill='both', expand=True)

            # Stats compactas
            primer_base = df_sueldo_plot["Sueldo_Base"].iloc[0]
            ultimo_val_base = df_sueldo_plot["Sueldo_Base"].iloc[-1]
            variacion_base = ultimo_val_base - primer_base
            var_pct_base = (ultimo_val_base / primer_base - 1) * 100 if primer_base > 0 else 0

            stats_text = f"Primer (Base): ${primer_base:,.0f} | Último (Base): ${ultimo_val_base:,.0f} | Variación (Base): ${variacion_base:,.0f} ({var_pct_base:+.1f}%)"

            if "Liquido_a_Pagar" in df_sueldo_plot.columns and not df_sueldo_plot["Liquido_a_Pagar"].isna().all():
                primer_liq_series = df_sueldo_plot["Liquido_a_Pagar"].dropna()
                if not primer_liq_series.empty:
                    primer_liq = primer_liq_series.iloc[0]
                    ultimo_val_liq = primer_liq_series.iloc[-1]
                    variacion_liq = ultimo_val_liq - primer_liq
                    var_pct_liq = (ultimo_val_liq / primer_liq - 1) * 100 if primer_liq > 0 else 0
                    stats_text += f"\nPrimer (Líq.): ${primer_liq:,.0f} | Último (Líq.): ${ultimo_val_liq:,.0f} | Variación (Líq.): ${variacion_liq:,.0f} ({var_pct_liq:+.1f}%)"

            tk.Label(section_chart, text=stats_text, font=('Arial', 10, 'bold'), bg='white', fg='#2c3e50').pack(pady=(6, 0))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def crear_pestaña_historial(self, notebook, df_persona):
        """Crea la pestaña de historial completo"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Historial Completo")

        # Título
        tk.Label(frame, text=f"Historial Completo - {df_persona['Nombre'].iloc[0]}", font=('Arial', 14, 'bold')).pack(pady=10)

        # Crear treeview para historial
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        cols = ("Período", "Cargo", "Área", "Sueldo Base", "Sueldo Líquido", "Años de Servicio")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=15)
        anchos = [80, 120, 120, 120, 120, 120]
        for i, col in enumerate(cols):
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=anchos[i])

        # Llenar con datos históricos
        df_ordenado = df_persona.sort_values(["Año", "Mes"], ascending=False)
        for _, row in df_ordenado.iterrows():
            sueldo_base = f"${row['Sueldo_Base']:,.0f}" if pd.notna(row.get('Sueldo_Base')) else "N/A"
            sueldo_liquido = f"${row['Liquido_a_Pagar']:,.0f}" if pd.notna(row.get('Liquido_a_Pagar')) else "N/A"
            anos_servicio = f"{row['Años_de_Servicio']:.1f}" if pd.notna(row.get('Años_de_Servicio')) else "N/A"
            tree.insert("", "end", values=(
                row.get("Pay_Period", ""),
                row.get("Cargo_Actual", ""),
                row.get("Nombre_Area", ""),
                sueldo_base,
                sueldo_liquido,
                anos_servicio
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
        if self.data_df is None or self.data_df.empty:
            messagebox.showwarning("Sin datos", "No hay información cargada.")
            return
        # Ventana secundaria
        win = tk.Toplevel(self.root)
        win.title("Evolución Salarial General")
        win.geometry("1000x700+100+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()

        # Título
        tk.Label(win, text="📈 Análisis de Evolución Salarial General", font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Frame de filtros
        filtros_frame = tk.LabelFrame(win, text="Seleccionar Análisis", font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', padx=15, pady=15)
        filtros_frame.pack(fill='x', padx=20, pady=10)

        # Filtro por área
        tk.Label(filtros_frame, text="🏢 Filtrar por Área:", bg='#f0f0f0', font=('Arial', 11, 'bold')).pack(anchor='w', pady=5)
        area_var = tk.StringVar(value="")
        areas = sorted(self.data_df["Nombre_Area"].dropna().unique())
        area_combo = ttk.Combobox(filtros_frame, textvariable=area_var, values=areas, width=30)
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
                # Agrupar por período
                df_grouped = df.groupby("Período").agg({
                    "Sueldo_Base": "mean",
                    "sueldo_base": "mean",
                    "person_id": "nunique"
                }).reset_index()
                ax.plot(df_grouped["Período"], df_grouped["Sueldo_Base"], marker='o', linewidth=2, label="Sueldo Teórico Promedio")
                ax.plot(df_grouped["Período"], df_grouped["sueldo_base"], marker='s', linewidth=2, label="Sueldo Liquidación Promedio")
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
        tk.Button(btn_frame, text="📈 Generar Gráfico", command=generar_grafico, bg='#27ae60', fg='white', font=('Arial', 12, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)
        tk.Button(btn_frame, text="❌ Cerrar", command=win.destroy, bg='#95a5a6', fg='white', font=('Arial', 12, 'bold'), relief='flat', padx=20, pady=8).pack(side='right', padx=10)

    def mostrar_resumen_areas(self):
        """Muestra resumen estadístico por áreas"""
        if self.data_df is None or self.data_df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para mostrar.")
            return
        # Usar solo último registro por persona
        df_ultimo = self.data_df.sort_values(["person_id", "Año", "Mes"]).groupby("person_id").tail(1)

        # Crear ventana de resumen
        win = tk.Toplevel(self.root)
        win.title("📊 Resumen por Área")
        win.geometry("800x600+200+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()
        tk.Label(win, text="📊 Resumen Estadístico por Área", font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Crear treeview
        columns = ('Área', 'Empleados', 'Sueldo Teórico Prom.', 'Sueldo Liquidación Prom.', 'Diferencia Prom.')
        tree = ttk.Treeview(win, columns=columns, show='headings', height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')

        # Calcular resumen por área
        resumen = df_ultimo.groupby('Nombre_Area').agg({
            'person_id': 'nunique',
            'Sueldo_Base': 'mean',
            'sueldo_base': 'mean'
        }).reset_index()
        resumen['Diferencia'] = resumen['Sueldo_Base'] - resumen['sueldo_base']

        # Llenar treeview
        for _, row in resumen.iterrows():
            tree.insert('', 'end', values=(
                row['Nombre_Area'],
                int(row['person_id']),
                f"${row['Sueldo_Base']:,.0f}",
                f"${row['sueldo_base']:,.0f}",
                f"${row['Diferencia']:,.0f}"
            ))
        tree.pack(fill='both', expand=True, padx=20, pady=10)
        tk.Button(win, text="❌ Cerrar", command=win.destroy, bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=10).pack(pady=15)

    def exportar_excel(self):
        """Exporta datos filtrados a Excel"""
        if self.data_df is None or self.data_df.empty:
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