"""
    Interfaz gráfica calculadora de sueldos
"""

#importaciones
import tkinter as tk
from tkinter import ttk
from controllers import services

class ConfigUI:
    
    def __init__(self):
        """
        INICIALIZA LA INTERFAZ GRÁFICA
        """
        self.root = tk.Tk()

        style = ttk.Style()
        style.configure("TNotebook", background='#ecf0f1')
        style.configure("TNotebook.Tab", padding=[15, 5])
        style.configure("TFrame", background='#ecf0f1')
        style.configure("TButton", font=('Arial', 10, 'bold'), relief='flat', background='#3498db', foreground='white')
        style.map("TButton", background=[('active', '#2980b9')])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        self._configuracion_ventana_principal()

        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
    def _configuracion_ventana_principal(self):
        """
        Configura la interfaz de usuario
        """
        self.root.title("Dashboard de Compensaciones")
        self.root.minsize(1300, 750)
        self.root.configure(bg='#ecf0f1')

        main_frame = tk.Frame(self.dashboard_frame, bg='#ecf0f1')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        #crea sección métricas
        self._crear_seccion_metricas(main_frame)
        #crea sección filtros
        self._crear_seccion_filtros(main_frame)
        #crea sección tabla
        self._crear_seccion_tabla(main_frame)
        
    def _crear_seccion_metricas(self, parent):
        metrics_frame = tk.LabelFrame(parent, text="Indicadores", font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=10, pady=10)
        metrics_frame.pack(fill='x', pady=(0, 8))
        row_metrics = tk.Frame(metrics_frame, bg='#ecf0f1')
        row_metrics.pack(fill='x')

        # Variables
        self.total_empleados = tk.StringVar(value="0")
        self.promedio_base = tk.StringVar(value="$0")
        #self.prom_liq_var = tk.StringVar(value="$0")
        self.promedio_anios = tk.StringVar(value="0 años")

        # Métricas
        self._crear_metrica(row_metrics, "Total Empleados", self.total_empleados, '#3498db')
        self._crear_metrica(row_metrics, "Sueldo Base Promedio", self.promedio_base, '#27ae60')
        #self._crear_metrica(row_metrics, "Líquido Promedio", self.prom_liq_var, '#f39c12')
        self._crear_metrica(row_metrics, "Antigüedad Promedio", self.promedio_anios, '#9b59b6')
    

    def _crear_metrica(self, parent, titulo, variable, color):
        box = tk.Frame(parent, bg=color, relief='raised', bd=2, width=150, height=80)
        box.pack(side='left', expand=True, fill='both', padx=5, pady=5)
        tk.Label(box, text=titulo, font=('Arial', 11, 'bold'), fg='white', bg=color).pack(pady=(10, 5))
        tk.Label(box, textvariable=variable, font=('Arial', 16, 'bold'), fg='white', bg=color).pack()

    def _crear_seccion_filtros(self, parent):
        main_split = tk.Frame(parent, bg='#ecf0f1')
        main_split.pack(fill='both', expand=True, pady=(5, 0))

        filtros_frame = tk.LabelFrame(main_split, text="Filtros", font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=8, pady=8)
        filtros_frame.pack(fill='x')

        # Primera fila de filtros
        fila1 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila1.pack(fill='x', pady=2)
        
        #label empresa
        tk.Label(fila1, text="Empresa:", bg='#ecf0f1').pack(side='left', padx=5)
        self.empresa_var = tk.StringVar(value="Todos")
        self.filtro_empresa = ttk.Combobox(fila1, textvariable=self.empresa_var, state="readonly", width=20)
        self.filtro_empresa.bind('<<ComboboxSelected>>', lambda event: services.actualizar_tabla(self))
        self.filtro_empresa.pack(side='left', padx=5)
        
        #label division
        tk.Label(fila1, text="División:", bg='#ecf0f1').pack(side='left', padx=5)
        self.division_var = tk.StringVar(value="Todos")
        self.filtro_division = ttk.Combobox(fila1, textvariable=self.division_var, state="readonly", width=20)
        self.filtro_division.bind('<<ComboboxSelected>>', lambda event: services.actualizar_tabla(self))
        self.filtro_division.pack(side='left', padx=5)
        
        #label área
        tk.Label(fila1, text="Área:", bg='#ecf0f1').pack(side='left', padx=5)
        self.area_var = tk.StringVar(value="Todos")
        self.filtro_areas = ttk.Combobox(fila1, textvariable=self.area_var, state="readonly", width=20)
        self.filtro_areas.bind('<<ComboboxSelected>>', lambda event: services.actualizar_tabla(self))
        self.filtro_areas.pack(side='left', padx=5)
                                                                                    
        # Segunda fila de filtros
        fila2 = tk.Frame(filtros_frame, bg='#ecf0f1')
        fila2.pack(fill='x', pady=5)
        
        # Búsqueda por nombre o rut
        tk.Label(fila2, text="Buscar por Nombre/RUT:", bg='#ecf0f1').pack(side='left', padx=5)
        self.busqueda_nombre = tk.StringVar()
        self.search_name_entry = ttk.Entry(fila2, textvariable=self.busqueda_nombre, width=30)
        self.search_name_entry.pack(side='left', padx=5)
        self.search_name_entry.bind('<KeyRelease>', lambda event: services.actualizar_tabla(self))
        
        # Búsqueda por cargo
        tk.Label(fila2, text="Buscar por Cargo:", bg='#ecf0f1').pack(side='left', padx=10)
        self.search_cargo_var = tk.StringVar()
        self.search_cargo_entry = ttk.Entry(fila2, textvariable=self.search_cargo_var, width=20)
        self.search_cargo_entry.pack(side='left', padx=5)
        self.search_cargo_entry.bind('<KeyRelease>', lambda event: services.actualizar_tabla(self))
        
        # Búsqueda por Jefatura
        tk.Label(fila2, text="Buscar por Jefatura:", bg='#ecf0f1').pack(side='left', padx=10)
        self.search_jefatura_var = tk.StringVar()
        self.search_jefatura_entry = ttk.Entry(fila2, textvariable=self.search_jefatura_var, width=20)
        self.search_jefatura_entry.pack(side='left', padx=5)
        self.search_jefatura_entry.bind('<KeyRelease>', lambda event: services.actualizar_tabla(self))

        tk.Button(fila2, text="Limpiar Filtros", command=lambda: services.limpiar_filtros(self), 
                  bg='#ed2b05', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=5)

    def _crear_seccion_tabla(self, parent):
        main_split = tk.Frame(parent, bg='#ecf0f1')
        main_split.pack(fill='both', expand=True, pady=(5, 0))

        tabla_frame = tk.LabelFrame(main_split, font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50', padx=8, pady=8)
        tabla_frame.pack(fill='both', expand=True, pady=(8, 0))
    
        # Frame para tabla y scrollbars
        tree_frame = tk.Frame(tabla_frame, bg='#ecf0f1')
        tree_frame.pack(fill='both', expand=True)

        # Columnas simplificadas para vista inicial
        cols = ("RUT", "Nombre", "Cargo", "Jefatura", "Sueldo Base", "Nivel", "Años de Servicio")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18, selectmode="extended")

        # Configurar columnas
        anchos = [50, 120, 200, 150, 50, 25, 50]
        for i, col in enumerate(cols):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=anchos[i])

        # Bind para doble clic
        self.tree.bind("<Double-1>", lambda event: services.abrir_ficha_persona(self))
        self.tree.bind('<<TreeviewSelect>>') #,self.verificar_seleccion_para_comparar)
         

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_v.set)

        # Pack
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')

        
    def run(self):
        self.root.mainloop()    
