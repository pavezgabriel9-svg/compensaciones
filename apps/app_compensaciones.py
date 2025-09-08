#Importaciones
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import traceback
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor

# Config BD
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "conexion_buk"

class ConnectionPool:
    """Pool de conexiones para optimizar acceso a BD"""
    def __init__(self, host, user, password, database, pool_size=3):
        self.pool = queue.Queue(maxsize=pool_size)
        self.pool_size = pool_size
        self.connection_kwargs = {
            'host': host,
            'user': user, 
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        
        # Llenar pool inicial
        for _ in range(pool_size):
            try:
                conn = pymysql.connect(**self.connection_kwargs)
                self.pool.put(conn)
            except Exception as e:
                print(f"Error creando conexión inicial: {e}")

    def get_connection(self):
        try:
            conn = self.pool.get(timeout=2)
            # Verificar si la conexión sigue activa
            conn.ping(reconnect=True)
            return conn
        except (queue.Empty, Exception):
            # Crear nueva conexión si no hay disponibles
            try:
                return pymysql.connect(**self.connection_kwargs)
            except Exception as e:
                print(f"Error creando nueva conexión: {e}")
                return None

    def return_connection(self, conn):
        try:
            if conn and not self.pool.full():
                self.pool.put(conn, timeout=1)
            elif conn:
                conn.close()
        except:
            if conn:
                conn.close()


class CompensaViewerOptimized:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana()
        
        # Inicializar variables
        self.employees_df = None
        self.cache = {}
        self.cache_timeout = 300  # 5 minutos
        self.search_timer = None
        self.is_loading = False
        
        # Pool de conexiones
        self.db_pool = ConnectionPool(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
        
        # Setup UI
        self.setup_ui()
        
        # Verificar BD y cargar datos optimizado
        threading.Thread(target=self.inicializar_datos, daemon=True).start()

    def _configurar_ventana(self):
        self.root.title("Dashboard de Compensaciones - Optimizado")
        self.root.minsize(1300, 750)
        self.root.geometry("1350x800+50+50")
        self.root.configure(bg='#ecf0f1')

    def inicializar_datos(self):
        """Inicialización completa en background"""
        try:
            self.mostrar_loading(True, "Verificando estructura BD...")
            self.verificar_estructura_bd()
            
            self.mostrar_loading(True, "Cargando datos básicos...")
            self.cargar_datos_optimizado()
            
        except Exception as e:
            print(f"Error en inicialización: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error inicializando: {e}"))
            self.root.after(0, lambda: self.mostrar_loading(False))

    # ------------------------------------------------------
    # Sistema de conexiones optimizado
    # ------------------------------------------------------
    def conectar_bd(self):
        """Usa connection pool"""
        return self.db_pool.get_connection()

    def cerrar_conexion_bd(self, conexion):
        """Devuelve conexión al pool"""
        if conexion:
            self.db_pool.return_connection(conexion)

    def verificar_estructura_bd(self):
        """Verifica qué columnas existen en las tablas principales"""
        conexion = self.conectar_bd()
        if not conexion:
            return
        
        try:
            cursor = conexion.cursor()
            
            # Verificar tablas principales
            tablas = ['historical_settlements', 'employees', 'employees_jobs', 'areas']
            for tabla in tablas:
                try:
                    cursor.execute(f"DESCRIBE {tabla}")
                    columns = [row[0] for row in cursor.fetchall()]
                    print(f"Columnas en {tabla}: {len(columns)} columnas")
                except Exception as e:
                    print(f"Error verificando tabla {tabla}: {e}")
            
        except Exception as e:
            print(f"Error verificando estructura: {e}")
        finally:
            self.cerrar_conexion_bd(conexion)

    # ------------------------------------------------------
    # Carga de datos optimizada
    # ------------------------------------------------------
    def obtener_total_registros(self):
        """Obtiene solo el conteo total sin cargar datos"""
        conexion = self.conectar_bd()
        if not conexion:
            return 0
        
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT COUNT(DISTINCT person_id) FROM employees WHERE status = 'activo'")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error obteniendo total: {e}")
            return 0
        finally:
            self.cerrar_conexion_bd(conexion)

    def cargar_datos_optimizado(self):
        """Carga inicial optimizada - solo empleados activos básicos"""
        try:
            # Obtener total para métricas
            total_empleados = self.obtener_total_registros()
            
            # Cargar datos básicos de empleados
            self.employees_df = self.obtener_empleados_basicos()
            
            # Actualizar UI en main thread
            self.root.after(0, lambda: self.actualizar_ui_post_carga(total_empleados))
            
        except Exception as e:
            print(f"Error en carga optimizada: {e}")
            self.root.after(0, lambda: self.mostrar_loading(False))

    def obtener_empleados_basicos(self):
        """Obtiene solo datos básicos necesarios para la vista principal"""
        conexion = self.conectar_bd()
        if not conexion:
            return pd.DataFrame()
        
        try:
            # Query optimizada - solo datos esenciales
            query = """
            SELECT DISTINCT
                e.person_id AS ID_Persona,
                e.rut AS RUT,
                e.full_name AS Nombre,
                COALESCE(e.gender, 'N/A') AS Género,
                e.area_id AS ID_Area_Actual,
                COALESCE(e.contract_type, 'N/A') AS Tipo_Contrato_Actual,
                e.active_since,
                
                -- Último cargo usando subquery optimizada
                (SELECT ej.role_name 
                 FROM employees_jobs ej 
                 WHERE ej.person_rut = e.rut 
                 AND ej.end_date IS NULL
                 ORDER BY ej.start_date DESC 
                 LIMIT 1) AS Cargo_Actual,
                
                -- Último sueldo base
                (SELECT ej.base_wage 
                 FROM employees_jobs ej 
                 WHERE ej.person_rut = e.rut 
                 AND ej.base_wage > 0 
                 AND ej.end_date IS NULL
                 ORDER BY ej.start_date DESC 
                 LIMIT 1) AS Sueldo_Base_Teorico,
                
                -- Área
                COALESCE(a.name, CONCAT('Área ', e.area_id)) AS Nombre_Area,
                
                -- Jefe actual
                (SELECT jefe.full_name 
                 FROM employees_jobs ej2
                 LEFT JOIN employees jefe ON ej2.boss_rut = jefe.rut
                 WHERE ej2.person_rut = e.rut 
                 AND ej2.end_date IS NULL
                 ORDER BY ej2.start_date DESC 
                 LIMIT 1) AS Nombre_Jefe
                
            FROM employees e
            LEFT JOIN areas a ON e.area_id = a.id
            WHERE e.status = 'activo'
            ORDER BY e.full_name
            LIMIT 2000
            """
            
            df = pd.read_sql(query, conexion)
            print(f"Carga básica completada: {len(df)} registros")
            
            # Post-procesamiento mínimo
            if not df.empty:
                # Calcular años de servicio
                df["Años_de_Servicio"] = (
                    pd.to_datetime("today").year - 
                    pd.to_datetime(df["active_since"], errors='coerce').dt.year
                ).fillna(0)
            
            return df
            
        except Exception as e:
            print(f"Error en carga básica: {e}")
            return pd.DataFrame()
        finally:
            self.cerrar_conexion_bd(conexion)

    def actualizar_ui_post_carga(self, total_empleados):
        """Actualiza UI después de carga en background"""
        try:
            if self.employees_df is None or self.employees_df.empty:
                messagebox.showwarning("Sin datos", "No se encontraron empleados activos.")
                self.mostrar_loading(False)
                return

            print(f"Actualizando UI con {len(self.employees_df)} empleados")

            # Poblar filtros
            self.poblar_filtros_basicos()
            
            # Actualizar métricas básicas
            self.actualizar_metricas_basicas(total_empleados)
            
            # Mostrar tabla
            self.actualizar_tabla_incremental(self.employees_df)
            
            self.mostrar_loading(False)
            
        except Exception as e:
            print(f"Error actualizando UI: {e}")
            self.mostrar_loading(False)

    def poblar_filtros_basicos(self):
        """Pobla combos de filtros con datos básicos"""
        try:
            if self.employees_df is not None and not self.employees_df.empty:
                # Áreas únicas
                areas = sorted([a for a in self.employees_df["Nombre_Area"].dropna().unique() if a])
                self.area_combo['values'] = ["Todos"] + areas
                
                # Reset valores
                self.area_var.set("Todos")
                
        except Exception as e:
            print(f"Error poblando filtros: {e}")

    def actualizar_metricas_basicas(self, total_empleados):
        """Actualiza métricas con datos básicos cargados"""
        try:
            df = self.employees_df
            if df is None or df.empty:
                self.total_emp_var.set("0")
                self.prom_teorico_var.set("$0")
                self.prom_liq_var.set("N/A")
                self.prom_antiguedad_var.set("0 años")
                return

            # Métricas básicas
            total = len(df)
            prom_teo = df["Sueldo_Base_Teorico"].fillna(0).mean()
            prom_antiguedad = df["Años_de_Servicio"].fillna(0).mean()

            self.total_emp_var.set(f"{total:,}")
            self.prom_teorico_var.set(f"${prom_teo:,.0f}")
            self.prom_liq_var.set("Carga completa...")  # Se carga bajo demanda
            self.prom_antiguedad_var.set(f"{prom_antiguedad:.1f} años")
            
        except Exception as e:
            print(f"Error actualizando métricas: {e}")

    # ------------------------------------------------------
    # Sistema de cache
    # ------------------------------------------------------
    def get_cached_query(self, query_key, query_func, *args, **kwargs):
        """Sistema de cache genérico para queries"""
        now = time.time()
        
        if query_key in self.cache:
            cached_data, timestamp = self.cache[query_key]
            if now - timestamp < self.cache_timeout:
                print(f"Cache HIT para {query_key}")
                return cached_data
        
        # Cache miss - ejecutar query
        print(f"Cache MISS para {query_key}")
        result = query_func(*args, **kwargs)
        self.cache[query_key] = (result, now)
        return result

    # ------------------------------------------------------
    # Sistema de filtros optimizado
    # ------------------------------------------------------
    def aplicar_filtros_optimizado(self):
        """Aplica filtros directamente en BD"""
        where_conditions = ["e.status = 'activo'"]
        params = []
        
        # Filtro por área
        if hasattr(self, 'area_var') and self.area_var.get() != "Todos":
            where_conditions.append("a.name = %s")
            params.append(self.area_var.get())
        
        # Filtro por búsqueda
        if hasattr(self, 'search_name_var'):
            search_term = self.search_name_var.get().strip()
            if search_term:
                palabras = search_term.split()
                condiciones_nombre = []
                for p in palabras:
                    condiciones_nombre.append("LOWER(e.full_name) LIKE %s")
                    params.append(f"%{p.lower()}%")
                
                # Condición: todas las palabras en nombre (AND) o RUT contiene
                where_conditions.append(f"(({ ' AND '.join(condiciones_nombre) }) OR e.rut LIKE %s)")
                params.append(f"%{search_term}%")
        
        return " AND ".join(where_conditions), params

    def actualizar_tabla_con_filtros_bd(self):
        """Actualiza tabla aplicando filtros en BD"""
        if self.is_loading:
            return
            
        def ejecutar_filtros():
            try:
                self.is_loading = True
                self.mostrar_loading(True, "Aplicando filtros...")
                
                where_clause, params = self.aplicar_filtros_optimizado()
                
                conexion = self.conectar_bd()
                if not conexion:
                    return
                
                query = f"""
                SELECT DISTINCT
                    e.rut AS RUT,
                    e.full_name AS Nombre,
                    (SELECT ej.role_name FROM employees_jobs ej 
                     WHERE ej.person_rut = e.rut AND ej.end_date IS NULL
                     ORDER BY ej.start_date DESC LIMIT 1) AS Cargo_Actual,
                    (SELECT jefe.full_name FROM employees_jobs ej2
                     LEFT JOIN employees jefe ON ej2.boss_rut = jefe.rut
                     WHERE ej2.person_rut = e.rut AND ej2.end_date IS NULL
                     ORDER BY ej2.start_date DESC LIMIT 1) AS Nombre_Jefe,
                    (SELECT ej.base_wage FROM employees_jobs ej 
                     WHERE ej.person_rut = e.rut AND ej.base_wage > 0 AND ej.end_date IS NULL
                     ORDER BY ej.start_date DESC LIMIT 1) AS Sueldo_Base_Teorico
                FROM employees e
                LEFT JOIN areas a ON e.area_id = a.id
                WHERE {where_clause}
                ORDER BY e.full_name
                LIMIT 1000
                """
                
                df_filtrado = pd.read_sql(query, conexion, params=params)
                self.cerrar_conexion_bd(conexion)
                
                # Actualizar UI en main thread
                self.root.after(0, lambda: self.actualizar_tabla_incremental(df_filtrado))
                
            except Exception as e:
                print(f"Error en filtros BD: {e}")
                self.root.after(0, lambda: self.mostrar_loading(False))
            finally:
                self.is_loading = False
        
        threading.Thread(target=ejecutar_filtros, daemon=True).start()

    # ------------------------------------------------------
    # Búsqueda con debounce
    # ------------------------------------------------------
    def setup_search_debounce(self):
        """Configura búsqueda con debounce"""
        if hasattr(self, 'search_name_entry'):
            self.search_name_entry.bind('<KeyRelease>', self.on_search_keyrelease)

    def on_search_keyrelease(self, event):
        """Maneja keyrelease con debounce"""
        if self.search_timer:
            self.root.after_cancel(self.search_timer)
        
        self.search_timer = self.root.after(800, self.buscar_con_debounce)

    def buscar_con_debounce(self):
        """Ejecuta búsqueda después del debounce"""
        search_term = self.search_name_var.get().strip()
        
        if len(search_term) >= 2 or search_term == "":
            self.actualizar_tabla_con_filtros_bd()

    # ------------------------------------------------------
    # Actualización incremental de UI
    # ------------------------------------------------------
    def actualizar_tabla_incremental(self, df, batch_size=100):
        """Actualiza tabla en lotes para no bloquear UI"""
        try:
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if df.empty:
                self.mostrar_loading(False)
                return
            
            def insert_batch(start_idx):
                try:
                    end_idx = min(start_idx + batch_size, len(df))
                    batch = df.iloc[start_idx:end_idx]
                    
                    for _, row in batch.iterrows():
                        sueldo = f"${row['Sueldo_Base_Teorico']:,.0f}" if pd.notna(row['Sueldo_Base_Teorico']) else "N/A"
                        jefe = row.get('Nombre_Jefe', 'N/A') if pd.notna(row.get('Nombre_Jefe')) else "N/A"
                        
                        self.tree.insert("", "end", values=(
                            row["RUT"], 
                            row["Nombre"], 
                            row.get("Cargo_Actual", "N/A") or "N/A",
                            jefe,
                            sueldo
                        ))
                    
                    # Continuar con siguiente lote
                    if end_idx < len(df):
                        self.root.after(20, lambda: insert_batch(end_idx))
                    else:
                        self.mostrar_loading(False)
                        
                except Exception as e:
                    print(f"Error en batch insert: {e}")
                    self.mostrar_loading(False)
            
            # Iniciar inserción por lotes
            insert_batch(0)
            
        except Exception as e:
            print(f"Error en actualización incremental: {e}")
            self.mostrar_loading(False)

    # ------------------------------------------------------
    # UI Loading
    # ------------------------------------------------------
    def mostrar_loading(self, show=True, message="🔄 Cargando..."):
        """Muestra/oculta indicador de carga"""
        if show:
            if not hasattr(self, 'loading_label') or not self.loading_label.winfo_exists():
                self.loading_label = tk.Label(self.root, text=message, 
                                            font=('Arial', 12, 'bold'), 
                                            bg='#f39c12', fg='white',
                                            relief='flat', pady=5)
                self.loading_label.pack(after=self.root.winfo_children()[0], fill='x')
            else:
                self.loading_label.config(text=message)
        else:
            if hasattr(self, 'loading_label') and self.loading_label.winfo_exists():
                self.loading_label.destroy()

    # ------------------------------------------------------
    # Interface de Usuario (adaptada)
    # ------------------------------------------------------
    def setup_ui(self):
        # Título barra
        title_frame = tk.Frame(self.root, bg='#2980b9', height=60)
        title_frame.pack(fill='x')
        title_label = tk.Label(title_frame, text="Dashboard de Compensaciones - Optimizado ⚡",
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

    def crear_seccion_metricas(self, parent):
        metrics_frame = tk.LabelFrame(parent, text="📊 Indicadores Principales",
                                      font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                      padx=10, pady=10)
        metrics_frame.pack(fill='x', pady=(0, 8))

        row_metrics = tk.Frame(metrics_frame, bg='#ecf0f1')
        row_metrics.pack(fill='x')

        # Variables
        self.total_emp_var = tk.StringVar(value="Cargando...")
        self.prom_teorico_var = tk.StringVar(value="Cargando...")
        self.prom_liq_var = tk.StringVar(value="Cargando...")
        self.prom_antiguedad_var = tk.StringVar(value="Cargando...")

        self._crear_metrica(row_metrics, "Total Empleados", self.total_emp_var, '#3498db')
        self._crear_metrica(row_metrics, "Sueldo Base Prom.", self.prom_teorico_var, '#27ae60')
        self._crear_metrica(row_metrics, "Sueldo Liquidación", self.prom_liq_var, '#f39c12')
        self._crear_metrica(row_metrics, "Antigüedad Prom.", self.prom_antiguedad_var, '#9b59b6')

    def _crear_metrica(self, parent, titulo, variable, color):
        box = tk.Frame(parent, bg=color, relief='raised', bd=2, width=150, height=80)
        box.pack(side='left', expand=True, fill='both', padx=5, pady=5)

        tk.Label(box, text=titulo, font=('Arial', 10, 'bold'), fg='white', bg=color).pack(pady=(8, 2))
        tk.Label(box, textvariable=variable, font=('Arial', 14, 'bold'), fg='white', bg=color).pack()

    def crear_seccion_principal(self, parent):
        main_split = tk.Frame(parent, bg='#ecf0f1')
        main_split.pack(fill='both', expand=True, pady=(5, 0))

        # Filtros
        filtros_frame = tk.LabelFrame(main_split, text="🔍 Filtros y Búsqueda Optimizada",
                                      font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                      padx=8, pady=8)
        filtros_frame.pack(fill='x')

        # Primera fila de filtros
        fila1 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila1.pack(fill='x', pady=2)

        tk.Label(fila1, text="Área:", bg='#ecf0f1', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        self.area_var = tk.StringVar(value="Todos")
        self.area_combo = ttk.Combobox(fila1, textvariable=self.area_var, state="readonly", width=25)
        self.area_combo.pack(side='left', padx=5)
        self.area_combo.bind('<<ComboboxSelected>>', lambda e: self.actualizar_tabla_con_filtros_bd())

        # Segunda fila - Búsqueda
        fila2 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila2.pack(fill='x', pady=5)

        tk.Label(fila2, text="🔎 Buscar (Nombre/RUT):", bg='#ecf0f1', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        self.search_name_var = tk.StringVar()
        self.search_name_entry = ttk.Entry(fila2, textvariable=self.search_name_var, width=30)
        self.search_name_entry.pack(side='left', padx=5)
        
        # Setup debounce después de crear el entry
        self.root.after(100, self.setup_search_debounce)

        tk.Button(fila2, text="🧹 Limpiar",
                  command=self.limpiar_filtros, bg='#95a5a6', fg='white',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=10)


        # Tabla
        tabla_frame = tk.Frame(main_split, bg='#ecf0f1')
        tabla_frame.pack(fill='both', expand=True, pady=(8, 0))

        tree_frame = tk.Frame(tabla_frame, bg='#ecf0f1')
        tree_frame.pack(fill='both', expand=True)

        # Columnas
        cols = ("RUT", "Nombre", "Cargo", "Jefatura", "Sueldo Base")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)

        anchos = [120, 250, 180, 180, 130]
        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=anchos[i])

        # Bind para doble clic
        self.tree.bind("<Double-1>", self.abrir_ficha_persona)

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar_h = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')

    def crear_seccion_acciones(self, parent):
        acciones_frame = tk.LabelFrame(parent, text="🚀 Acciones Rápidas",
                                       font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50',
                                       padx=10, pady=10)
        acciones_frame.pack(fill='x', pady=(8, 0))

        btn_frame = tk.Frame(acciones_frame, bg='#ecf0f1')
        btn_frame.pack()

        tk.Button(btn_frame, text="🔧 Test Conexión BD",
                  command=self.test_conexion,
                  bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=15, pady=6).pack(side='left', padx=8)

        tk.Button(btn_frame, text="📊 Resumen por Área",
                  command=self.mostrar_resumen_areas,
                  bg='#e67e22', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=15, pady=6).pack(side='left', padx=8)

        tk.Button(btn_frame, text="📥 Exportar Vista Actual",
                  command=self.exportar_excel,
                  bg='#16a085', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=15, pady=6).pack(side='left', padx=8)

        tk.Button(btn_frame, text="🔄 Recargar Datos",
                  command=self.recargar_datos,
                  bg='#8e44ad', fg='white', font=('Arial', 10, 'bold'),
                  relief='flat', padx=15, pady=6).pack(side='left', padx=8)

    # ------------------------------------------------------
    # Funciones de acciones
    # ------------------------------------------------------
    def limpiar_filtros(self):
        """Limpia filtros y recarga tabla básica"""
        self.area_var.set("Todos")
        self.search_name_var.set("")
        if self.employees_df is not None:
            self.actualizar_tabla_incremental(self.employees_df)

    def test_conexion(self):
        """Prueba la conexión a BD"""
        conexion = self.conectar_bd()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("SELECT COUNT(*) FROM employees WHERE status = 'activo'")
                total = cursor.fetchone()[0]
                messagebox.showinfo("✅ Conexión OK", f"Conexión exitosa.\nEmpleados activos: {total:,}")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Error consultando: {e}")
            finally:
                self.cerrar_conexion_bd(conexion)
        else:
            messagebox.showerror("❌ Sin conexión", "No se pudo conectar a la base de datos")

    def recargar_datos(self):
        """Recarga todos los datos"""
        # Limpiar cache
        self.cache.clear()
        
        # Recargar en background
        threading.Thread(target=self.inicializar_datos, daemon=True).start()

    def abrir_ficha_persona(self, event):
        """Abre ficha detallada con carga lazy del histórico"""
        item = self.tree.focus()
        if not item:
            return
        
        values = self.tree.item(item, "values")
        rut = values[0]
        
        # Cargar histórico en background
        threading.Thread(target=lambda: self.mostrar_ficha_persona_completa(rut), daemon=True).start()

    def cargar_historico_persona(self, rut):
        """Carga histórico específico de una persona (lazy loading) - VERSIÓN CORREGIDA"""
        cache_key = f"historico_{rut}"
        
        def query_historico():
            conexion = self.conectar_bd()
            if not conexion:
                return pd.DataFrame()
            
            try:
                query = """
                SELECT 
                    hs.periodo AS Período,
                    YEAR(STR_TO_DATE(hs.periodo, '%%m-%%Y')) AS Año,
                    MONTH(STR_TO_DATE(hs.periodo, '%%m-%%Y')) AS Mes,
                    COALESCE(hs.ingreso_bruto, 0) AS Ingreso_Bruto,
                    COALESCE(hs.liquido_a_pagar, 0) AS Sueldo_Liquidacion,
                    COALESCE(hs.dias_trabajados, 0) AS Dias_Trabajados,
                    COALESCE(hs.dias_no_trabajados, 0) AS Dias_No_Trabajados
                FROM historical_settlements hs
                WHERE hs.rut = %s
                ORDER BY YEAR(STR_TO_DATE(hs.periodo, '%%m-%%Y')) DESC, 
                        MONTH(STR_TO_DATE(hs.periodo, '%%m-%%Y')) DESC
                LIMIT 24
                """
                df = pd.read_sql(query, conexion, params=[rut])
                
                # CAMBIO IMPORTANTE: Mantener el orden DESC para mostrar los más recientes primero
                # NO reordenar aquí - ya viene ordenado correctamente desde la BD
                return df
                
            except Exception as e:
                print(f"Error cargando histórico para {rut}: {e}")
                return pd.DataFrame()
            finally:
                self.cerrar_conexion_bd(conexion)
    
        return self.get_cached_query(cache_key, query_historico)
    
    def mostrar_ficha_persona_completa(self, rut):
        """Muestra ficha completa con histórico"""
        try:
            # Obtener datos básicos de la persona
            df_persona = self.employees_df[self.employees_df["RUT"] == rut] if self.employees_df is not None else pd.DataFrame()
            
            if df_persona.empty:
                self.root.after(0, lambda: messagebox.showwarning("Sin datos", f"No se encontraron datos para RUT: {rut}"))
                return

            persona = df_persona.iloc[0]
            
            # Cargar histórico
            historico_df = self.cargar_historico_persona(rut)
            
            # Mostrar ventana en main thread
            self.root.after(0, lambda: self.crear_ventana_ficha(persona, historico_df))
            
        except Exception as e:
            print(f"Error en ficha persona: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error cargando ficha: {e}"))

    def crear_ventana_ficha(self, persona, historico_df):
        """Crea ventana de ficha detallada"""
        win = tk.Toplevel(self.root)
        win.title(f"📋 Ficha Completa - {persona['Nombre']}")
        win.geometry("700x600+250+150")
        win.configure(bg='#f8f9fa')
        win.grab_set()

        # Frame principal con scroll
        main_canvas = tk.Canvas(win, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg='#f8f9fa')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Información básica
        info_frame = tk.LabelFrame(scrollable_frame, text="👤 Información Personal y Laboral", 
                                  font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#2c3e50', padx=15, pady=10)
        info_frame.pack(fill='x', padx=15, pady=10)

        info_text = f"""
📄 DATOS PERSONALES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• RUT: {persona.get('RUT', 'N/A')}
• Nombre: {persona.get('Nombre', 'N/A')}
• Género: {persona.get('Género', 'N/A')}
• Años de Servicio: {persona.get('Años_de_Servicio', 0):.1f} años

💼 INFORMACIÓN LABORAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Cargo: {persona.get('Cargo_Actual', 'N/A')}
• Área: {persona.get('Nombre_Area', 'N/A')}
• Jefe: {persona.get('Nombre_Jefe', 'Sin Asignar')}
• Tipo de Contrato: {persona.get('Tipo_Contrato_Actual', 'N/A')}
• Sueldo Base Actual: ${persona.get('Sueldo_Base_Teorico', 0):,.0f}
        """

        text_widget = tk.Text(info_frame, wrap=tk.WORD, font=('Consolas', 10), height=12, bg='#ffffff')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')

        # Histórico si existe
        if not historico_df.empty:
            hist_frame = tk.LabelFrame(scrollable_frame, text="📈 Histórico de Liquidaciones (Últimos 24 meses)", 
                                      font=('Arial', 12, 'bold'), bg='#f8f9fa', fg='#2c3e50', padx=15, pady=10)
            hist_frame.pack(fill='both', expand=True, padx=15, pady=10)

            # Tabla de histórico
            hist_cols = ("Período", "Ingreso Bruto", "Líquido a Pagar", "Días Trabajados")
            hist_tree = ttk.Treeview(hist_frame, columns=hist_cols, show="headings", height=8)
            
            for col in hist_cols:
                hist_tree.heading(col, text=col)
                hist_tree.column(col, width=120, anchor='center')

            for _, row in historico_df.iterrows():
                hist_tree.insert("", "end", values=(
                    row.get('Período', 'N/A'),
                    f"${row.get('Ingreso_Bruto', 0):,.0f}",
                    f"${row.get('Sueldo_Liquidacion', 0):,.0f}",
                    row.get('Dias_Trabajados', 0)
                ))

            hist_tree.pack(fill='both', expand=True)

        # Botones
        btn_frame = tk.Frame(scrollable_frame, bg='#f8f9fa')
        btn_frame.pack(fill='x', padx=15, pady=15)

        tk.Button(btn_frame, text="📊 Ver Evolución Gráfica", 
                 command=lambda: self.mostrar_grafico_persona(persona['RUT'], historico_df),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="❌ Cerrar", command=win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=10)

        # Pack canvas y scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def mostrar_grafico_persona(self, rut, historico_df):
        """Muestra gráfico de evolución salarial de una persona"""
        if historico_df.empty:
            messagebox.showinfo("Sin datos", "No hay datos históricos para mostrar gráfico")
            return

        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Crear ventana para gráfico
            graf_win = tk.Toplevel(self.root)
            graf_win.title(f"📈 Evolución Salarial - RUT: {rut}")
            graf_win.geometry("800x500+300+200")
            
            # Preparar datos
            df_plot = historico_df.copy()
            df_plot = df_plot.sort_values(['Año', 'Mes'])
            df_plot['Fecha'] = pd.to_datetime(df_plot[['Año', 'Mes']].assign(day=1))
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.plot(df_plot['Fecha'], df_plot['Sueldo_Liquidacion'], 
                   marker='o', linewidth=2, markersize=4, color='#3498db', label='Líquido a Pagar')
            ax.plot(df_plot['Fecha'], df_plot['Ingreso_Bruto'], 
                   marker='s', linewidth=2, markersize=4, color='#27ae60', label='Ingreso Bruto')
            
            ax.set_title(f'Evolución Salarial - RUT: {rut}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Período')
            ax.set_ylabel('Monto ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Formatear ejes
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            plt.tight_layout()
            
            # Integrar con tkinter
            canvas = FigureCanvasTkAgg(fig, graf_win)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
            
            tk.Button(graf_win, text="❌ Cerrar", command=graf_win.destroy,
                     bg='#95a5a6', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
            
        except ImportError:
            messagebox.showwarning("Módulo faltante", "Se requiere matplotlib para mostrar gráficos")
        except Exception as e:
            messagebox.showerror("Error", f"Error creando gráfico: {e}")

    def mostrar_resumen_areas(self):
        """Muestra resumen estadístico por áreas con datos optimizados"""
        if self.employees_df is None or self.employees_df.empty:
            messagebox.showinfo("Sin datos", "No hay datos para mostrar.")
            return

        def calcular_resumen():
            try:
                # Calcular resumen
                resumen = self.employees_df.groupby('Nombre_Area').agg({
                    'ID_Persona': 'nunique',
                    'Sueldo_Base_Teorico': lambda x: x.fillna(0).mean(),
                    'Años_de_Servicio': lambda x: x.fillna(0).mean()
                }).reset_index()
                
                resumen.columns = ['Area', 'Total_Empleados', 'Sueldo_Promedio', 'Antiguedad_Promedio']
                resumen = resumen.sort_values('Total_Empleados', ascending=False)
                
                # Mostrar en UI
                self.root.after(0, lambda: self.crear_ventana_resumen_areas(resumen))
                
            except Exception as e:
                print(f"Error calculando resumen: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error calculando resumen: {e}"))

        threading.Thread(target=calcular_resumen, daemon=True).start()

    def crear_ventana_resumen_areas(self, resumen):
        """Crea ventana de resumen por áreas"""
        win = tk.Toplevel(self.root)
        win.title("📊 Resumen Detallado por Área")
        win.geometry("900x600+200+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()

        # Título
        tk.Label(win, text="📊 Análisis por Área de Trabajo", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Frame para tabla
        table_frame = tk.Frame(win, bg='#f0f0f0')
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Treeview mejorado
        columns = ('Área', 'Empleados', 'Sueldo Promedio', 'Antigüedad Promedio')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        tree.column('Área', width=250)
        tree.column('Empleados', width=100, anchor='center')
        tree.column('Sueldo Promedio', width=150, anchor='center')
        tree.column('Antigüedad Promedio', width=150, anchor='center')
        
        for col in columns:
            tree.heading(col, text=col)

        # Llenar datos
        for _, row in resumen.iterrows():
            tree.insert('', 'end', values=(
                row['Area'],
                f"{row['Total_Empleados']:,}",
                f"${row['Sueldo_Promedio']:,.0f}",
                f"{row['Antiguedad_Promedio']:.1f} años"
            ))

        # Scrollbar
        scrollbar_res = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_res.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar_res.pack(side='right', fill='y')

        # Estadísticas generales
        stats_frame = tk.LabelFrame(win, text="📈 Estadísticas Generales", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        stats_frame.pack(fill='x', padx=20, pady=10)

        total_areas = len(resumen)
        total_empleados = resumen['Total_Empleados'].sum()
        sueldo_general = resumen['Sueldo_Promedio'].mean()

        stats_text = f"🏢 Total de Áreas: {total_areas}  |  👥 Total Empleados: {total_empleados:,}  |  💰 Sueldo Promedio General: ${sueldo_general:,.0f}"
        tk.Label(stats_frame, text=stats_text, font=('Arial', 10), bg='#f0f0f0').pack(pady=5)

        # Botón cerrar
        tk.Button(win, text="❌ Cerrar", command=win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(pady=15)

    def exportar_excel(self):
        """Exporta la vista actual a Excel"""
        try:
            if self.employees_df is None or self.employees_df.empty:
                messagebox.showwarning("Sin datos", "No hay datos para exportar.")
                return

            # Obtener datos filtrados actuales
            df_export = self.aplicar_filtros_memoria()
            
            if df_export.empty:
                messagebox.showwarning("Sin datos", "No hay datos que coincidan con los filtros actuales.")
                return

            # Preparar datos para exportación
            df_export_clean = df_export[[
                'RUT', 'Nombre', 'Cargo_Actual', 'Nombre_Area', 'Nombre_Jefe',
                'Sueldo_Base_Teorico', 'Años_de_Servicio', 'Tipo_Contrato_Actual'
            ]].copy()
            
            df_export_clean.columns = [
                'RUT', 'Nombre Completo', 'Cargo', 'Área', 'Jefatura',
                'Sueldo Base', 'Años Servicio', 'Tipo Contrato'
            ]

            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"compensaciones_export_{timestamp}.xlsx"
            
            # Exportar
            df_export_clean.to_excel(filename, index=False, sheet_name='Empleados')
            messagebox.showinfo("✅ Exportación Exitosa", 
                              f"Se exportaron {len(df_export_clean):,} registros a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error exportando a Excel:\n{e}")

    def aplicar_filtros_memoria(self):
        """Aplica filtros en memoria para exportación"""
        if self.employees_df is None:
            return pd.DataFrame()
            
        df = self.employees_df.copy()
        
        # Filtro por área
        if hasattr(self, 'area_var') and self.area_var.get() != "Todos":
            df = df[df["Nombre_Area"] == self.area_var.get()]
        
        # Filtro por búsqueda
        if hasattr(self, 'search_name_var'):
            search_term = self.search_name_var.get().strip()
            if search_term:
                mask_nombre = df["Nombre"].str.contains(search_term, case=False, na=False)
                mask_rut = df["RUT"].astype(str).str.contains(search_term, case=False, na=False)
                df = df[mask_nombre | mask_rut]
        
        return df

    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            # Limpiar recursos
            if hasattr(self, 'db_pool'):
                # Cerrar todas las conexiones del pool
                while not self.db_pool.pool.empty():
                    try:
                        conn = self.db_pool.pool.get_nowait()
                        conn.close()
                    except:
                        break
            
            self.root.destroy()
            
        except Exception as e:
            print(f"Error cerrando aplicación: {e}")
            self.root.destroy()

# ----------------------------------------------------------
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = CompensaViewerOptimized(root)
        
        # Manejar cierre de ventana
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("🚀 Aplicación optimizada iniciada")
        print("💡 Características activas:")
        print("   • Carga lazy de datos")
        print("   • Connection pooling")  
        print("   • Cache inteligente")
        print("   • Búsqueda con debounce")
        print("   • Threading para operaciones pesadas")
        print("   • Actualización incremental de UI")
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error fatal: {e}")
        messagebox.showerror("Error Fatal", f"No se pudo inicializar la aplicación:\n{e}")