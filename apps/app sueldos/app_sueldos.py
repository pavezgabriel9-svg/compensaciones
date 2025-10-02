#-----------------------------------------------------------
#                           Importaciones
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, List, Any, Optional

#-----------------------------------------------------------
#             iniciando App
#-----------------------------------------------------------

class CalculadoraSueldos:
    """Calculadora de sueldos"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana_principal()
        
        # valores por defecto
        self.parametros_default = {
            "ingreso_minimo": 529_000,
            "valor_uf": 39_149,
            "tope_imponible_uf": 87.8,
            "tasa_afp": 0.1049,
            "tasa_salud": 0.07,
            "tasa_cesant": 0.006,
            "factor_gratificacion": 4.75,
            "porcentaje_gratificacion": 0.25
        }

        # Tramos de impuesto por defecto
        self.tramos_default = [
            {"desde": 0,          "hasta": 926734.50,  "tasa": 0.00, "rebaja":       0.0},
            {"desde": 926734.51,  "hasta": 2059410.00, "tasa": 0.04, "rebaja":   37069.38},
            {"desde": 2059410.01, "hasta": 3432350.00, "tasa": 0.08, "rebaja":  119445.78},
            {"desde": 3432350.01, "hasta": 4805290.00, "tasa": 0.135,"rebaja":  308225.03},
            {"desde": 4805290.01, "hasta": 6178230.00, "tasa": 0.23, "rebaja":  764727.58},
            {"desde": 6178230.01, "hasta": 8237640.00, "tasa": 0.304,"rebaja": 1221916.60},
            {"desde": 8237640.01, "hasta": 21280570.00,"tasa": 0.35, "rebaja": 1600848.04},
            {"desde": 21280570.01,"hasta": float('inf'),"tasa": 0.40,"rebaja": 2664876.54},
]

        # Inicializar
        self.cargar_configuracion()
        self.inicializar_variables()
        self.setup_ui()

        self._validar_configuracion_inicial()
    
    def _validar_configuracion_inicial(self):
        """Valida que la configuración inicial sea correcta"""
        try:
            # Validar tramos de impuesto
            if not self.tramos_impuesto:
                raise ValueError("No hay tramos de impuesto configurados")
            
            # Verificar que los tramos tengan estructura correcta
            for i, tramo in enumerate(self.tramos_impuesto):
                campos_requeridos = ['desde', 'hasta', 'tasa', 'rebaja']
                for campo in campos_requeridos:
                    if campo not in tramo:
                        raise ValueError(f"Tramo {i} no tiene campo '{campo}'")
                    if not isinstance(tramo[campo], (int, float)):
                        raise ValueError(f"Campo '{campo}' en tramo {i} no es numérico")
            
            # Test básico del cálculo de impuestos
            # test_impuesto = self.impuesto_unico(1000000)  # 1 millón de prueba
            # if test_impuesto is None:
            #     raise ValueError("Error en cálculo de impuestos de prueba")
                
            # print("✅ Configuración inicial validada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error de Configuración", 
                            f"Problema con la configuración inicial:\n{e}\n\n"
                            "La aplicación puede no funcionar correctamente.")
            print(f"❌ Error en validación inicial: {e}")

    def _configurar_ventana_principal(self):
        """Configura la ventana principal"""
        self.root.title("Calculadora de Sueldos")
        self.root.minsize(450, 600)
        self.root.geometry("480x700+50+50")
        self.root.configure(bg='#f0f0f0')

    def inicializar_variables(self):
        """Inicializa todas las variables de la interfaz"""
        self.sueldo_liquido_var = tk.StringVar()
        # Variables para el sistema de salud
        self.tipo_salud_var = tk.StringVar(value="fonasa")  # "fonasa" o "isapre"
        self.valor_isapre_uf_var = tk.StringVar(value="4.78")  # Valor por defecto en UF
        self.movilizacion_var = tk.StringVar(value="40.000")
        self.bonos: List[Dict[str, Any]] = []
        self.bono_nombre_var = tk.StringVar()
        self.bono_monto_var = tk.StringVar()
        self.bono_imponible_var = tk.BooleanVar(value=True)

    def cargar_configuracion(self):
        """Carga la configuración desde archivo o usa valores por defecto"""
        config_file = "config_sueldos.json"
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.parametros = config.get("parametros", self.parametros_default.copy())
                    self.tramos_impuesto = config.get("tramos_impuesto", self.tramos_default.copy())
                    print("✅ Configuración cargada desde archivo")
            else:
                self._usar_configuracion_default()
                print("📋 Usando configuración por defecto")
        except Exception as e:
            print(f"⚠️ Error cargando configuración: {e}")
            self._usar_configuracion_default()

    def _usar_configuracion_default(self):
        """Establece la configuración por defecto"""
        self.parametros = self.parametros_default.copy()
        self.tramos_impuesto = self.tramos_default.copy()

    def guardar_configuracion(self) -> bool:
        """Guarda la configuración actual en archivo"""
        config_file = "config_sueldos.json"
        try:
            config = {
                "parametros": self.parametros,
                "tramos_impuesto": self.tramos_impuesto
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {e}")
            return False

#-----------------------------------------------------------
#             Creación de Interfaz de Usuario
#-----------------------------------------------------------

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self._crear_titulo()
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Secciones
        self.crear_seccion_entradas(main_frame)
        self.crear_seccion_bonos(main_frame)
        self._crear_boton_calcular(main_frame)
        self._crear_info_parametros(main_frame)

    def _crear_titulo(self):
        """Crea el título de la aplicación"""
        title_frame = tk.Frame(self.root, bg='#FF0000', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Calculadora de Sueldos", 
                              font=('Arial', 14, 'bold'), fg='white', bg='#FF0000')
        title_label.pack(expand=True, pady=10)

    def _crear_boton_calcular(self, parent):
        """Crea el botón de calcular"""
        calc_button = tk.Button(parent, text="Calcular Sueldo Base", 
                               command=self.calcular, font=('Arial', 13, 'bold'),
                               bg='#008000', fg='#111111', relief='flat', padx=10, pady=10)
        calc_button.pack(pady=10, fill='x')

    def _crear_info_parametros(self, parent):
        """Crea la información de parámetros"""
        self.info_label = tk.Label(parent, text=self.get_info_parametros(), 
                                  font=('Arial', 8), bg='#f0f0f0', fg='#7f8c8d', justify='left')
        self.info_label.pack(pady=(0, 5), fill='x')

    def crear_seccion_entradas(self, parent):
        """Crea la sección de entradas principales"""
        input_frame = tk.LabelFrame(parent, text="Datos de Entrada", 
                                   font=('Arial', 11, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))

        # Sueldo líquido deseado
        self._crear_campo_sueldo(input_frame)
        
        # AFP
        self._crear_campo_afp(input_frame)
        
        # Sistema de Salud
        self._crear_campo_salud(input_frame)
        
        # Movilización
        self._crear_campo_movilizacion(input_frame)
        
        # Botón parámetros avanzados
        self._crear_boton_parametros(input_frame)

    def _crear_campo_sueldo(self, parent):
        """Crea el campo de sueldo líquido"""
        tk.Label(parent, fg='#000000' ,text="Sueldo Líquido Deseado ($):", 
                font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        sueldo_entry = tk.Entry(parent, textvariable=self.sueldo_liquido_var, 
                               font=('Arial', 12), width=13)
        sueldo_entry.grid(row=0, column=1, padx=5, pady=5)
        sueldo_entry.bind('<KeyRelease>', self._format_currency_sueldo)

    def _crear_campo_afp(self, parent):
        """Crea el campo de AFP estático"""
        tk.Label(parent, text="AFP:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=1, column=0, sticky='e', padx=5, pady=5)
        
        # Label estático que muestra la tasa de AFP configurada
        self.afp_label = tk.Label(parent, text=f"{self.parametros['tasa_afp']*100:.2f}%", 
                                 font=('Arial', 12), bg='white', fg='#2c3e50', 
                                 relief='solid', borderwidth=1, padx=10, pady=3, width=16)
        self.afp_label.grid(row=1, column=1, padx=5, pady=5)

    def _crear_campo_salud(self, parent):
        """Crea el campo de sistema de salud con checkboxes"""
        tk.Label(parent, text="Salud:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=2, column=0, sticky='ne', padx=5, pady=5)
        
        # Frame para los checkboxes y campo UF
        salud_frame = tk.Frame(parent, bg='#f0f0f0')
        salud_frame.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Checkbox Fonasa
        self.fonasa_check = tk.Radiobutton(salud_frame, text=f"Fonasa ({self.parametros['tasa_salud']*100:.1f}%)", 
                                          variable=self.tipo_salud_var, value="fonasa",
                                          bg='#f0f0f0', font=('Arial', 9),
                                          command=self._actualizar_interfaz_salud)
        self.fonasa_check.pack(anchor='w')
        
        # Checkbox Isapre con campo UF
        isapre_frame = tk.Frame(salud_frame, bg='#f0f0f0')
        isapre_frame.pack(anchor='w', fill='x')
        
        self.isapre_check = tk.Radiobutton(isapre_frame, text="Isapre", 
                                          variable=self.tipo_salud_var, value="isapre",
                                          bg='#f0f0f0', font=('Arial', 9),
                                          command=self._actualizar_interfaz_salud)
        self.isapre_check.pack(side='left')
        
        # Campo para valor UF de Isapre
        tk.Label(isapre_frame, text="UF:", bg='#f0f0f0', font=('Arial', 9)).pack(side='left', padx=(5, 2))
        self.isapre_uf_entry = tk.Entry(isapre_frame, textvariable=self.valor_isapre_uf_var, 
                                       width=6, font=('Arial', 9), state='disabled')
        self.isapre_uf_entry.pack(side='left', padx=(0, 5))
        
        # Label para mostrar valor en pesos
        self.isapre_pesos_label = tk.Label(isapre_frame, text="", bg='#f0f0f0', 
                                          font=('Arial', 8), fg='#7f8c8d')
        self.isapre_pesos_label.pack(side='left')
        
        # Inicializar estado
        self._actualizar_interfaz_salud()
        
        # Bind para actualizar valor en pesos cuando cambie UF
        self.valor_isapre_uf_var.trace('w', lambda *args: self._actualizar_valor_isapre_pesos())

    def _actualizar_interfaz_salud(self):
        """Actualiza la interfaz según el tipo de salud seleccionado"""
        if self.tipo_salud_var.get() == "fonasa":
            self.isapre_uf_entry.config(state='disabled')
            self.isapre_pesos_label.config(text="")
        else:  # isapre
            self.isapre_uf_entry.config(state='normal')
            self._actualizar_valor_isapre_pesos()

    def _actualizar_valor_isapre_pesos(self):
        """Actualiza el valor en pesos de la Isapre"""
        try:
            if self.tipo_salud_var.get() == "isapre":
                uf_valor = float(self.valor_isapre_uf_var.get())
                pesos = uf_valor * self.parametros['valor_uf']
                self.isapre_pesos_label.config(text=f"(${pesos:,.0f})".replace(',', '.'))
            else:
                self.isapre_pesos_label.config(text="")
        except (ValueError, TypeError):
            self.isapre_pesos_label.config(text="(Error)")

    def get_cotizacion_salud(self, imponible: float) -> tuple[float, str]:
        """
        Calcula la cotización de salud según el tipo seleccionado
        Retorna: (monto_cotizacion, descripcion_texto)
        """
        if self.tipo_salud_var.get() == "fonasa":
            # Fonasa: porcentaje del imponible con tope
            tope_imponible_pesos = self.parametros["tope_imponible_uf"] * self.parametros["valor_uf"]
            cotizacion = min(imponible * self.parametros["tasa_salud"], tope_imponible_pesos * self.parametros["tasa_salud"])
            descripcion = f"Fonasa ({self.parametros['tasa_salud']*100:.1f}%)"
            return cotizacion, descripcion
        else:
            # Isapre: valor fijo en UF convertido a pesos
            try:
                uf_valor = float(self.valor_isapre_uf_var.get())
                cotizacion = uf_valor * self.parametros["valor_uf"]
                descripcion = f"Isapre ({uf_valor} UF)"
                return cotizacion, descripcion
            except (ValueError, TypeError):
                return 0.0, "Isapre (Error en UF)"

    def _crear_campo_movilizacion(self, parent):
        """Crea el campo de movilización"""
        tk.Label(parent, text="Movilización ($):", font=('Arial', 10), bg='#f0f0f0').grid(
            row=3, column=0, sticky='e', padx=5, pady=5)
        mov_entry = tk.Entry(parent, textvariable=self.movilizacion_var, 
                            font=('Arial', 10), width=13)
        mov_entry.grid(row=3, column=1, padx=5, pady=5)
        mov_entry.bind('<KeyRelease>', self._format_currency_movilizacion)

    def _crear_boton_parametros(self, parent):
        """Crea el botón de parámetros avanzados"""
        param_btn = tk.Button(parent, text="Parámetros avanzados", 
                             command=self.abrir_parametros, font=('Arial', 10, 'bold'),
                             bg='#e67e22', fg='white', relief='flat', padx=10, pady=6)
        param_btn.grid(row=6, column=0, columnspan=2, pady=10)

    def crear_seccion_bonos(self, parent):
        """Crea la sección de bonos"""
        bonos_frame = tk.LabelFrame(parent, text="Bonos", 
                                   font=('Arial', 11, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        bonos_frame.pack(fill='x', pady=(0, 10))

        # Formulario para agregar bono
        self._crear_formulario_bono(bonos_frame)
        
        # Lista de bonos
        self._crear_lista_bonos(bonos_frame)

    def _crear_formulario_bono(self, parent):
        """Crea el formulario para agregar bonos"""
        tk.Label(parent, text="Nombre:", bg='#f0f0f0', font=('Arial', 9)).grid(
            row=0, column=0, padx=2, pady=5, sticky='e')
        tk.Entry(parent, textvariable=self.bono_nombre_var, width=13, font=('Arial', 9)).grid(
            row=0, column=1, padx=2, pady=5)

        tk.Label(parent, text="Monto ($):", bg='#f0f0f0', font=('Arial', 9)).grid(
            row=0, column=2, padx=2, pady=5, sticky='e')
        bono_entry = tk.Entry(parent, textvariable=self.bono_monto_var, width=10, font=('Arial', 9))
        bono_entry.grid(row=0, column=3, padx=2, pady=5)
        bono_entry.bind('<KeyRelease>', self._format_currency_bono)

        tk.Checkbutton(parent, text="Imponible", variable=self.bono_imponible_var, 
                      bg='#f0f0f0', font=('Arial', 9)).grid(row=0, column=4, padx=2, pady=5)

        tk.Button(parent, text="➕", command=self.agregar_bono, 
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'), relief='flat', width=3).grid(
                 row=0, column=5, padx=2, pady=5)

    def _crear_lista_bonos(self, parent):
        """Crea la lista de bonos"""
        self.bonos_listbox = tk.Listbox(parent, width=55, height=3, font=('Arial', 9))
        self.bonos_listbox.grid(row=1, column=0, columnspan=6, padx=2, pady=5, sticky='ew')
        
        tk.Button(parent, text="Eliminar Bono", command=self.eliminar_bono, 
                 bg='#c0392b', fg='white', font=('Arial', 9, 'bold'), relief='flat').grid(
                 row=2, column=0, columnspan=6, pady=5)

    def get_info_parametros(self) -> str:
        """Muestra información actual de parámetros"""
        #tope_imponible_pesos = self.parametros["tope_imponible_uf"] * self.parametros["valor_uf"]
        tope_grat = self.parametros["factor_gratificacion"] * self.parametros["ingreso_minimo"] / 12
        
        ancho = 100
        titulo = "Valores Utilizados".center(ancho)

        return (f"{titulo} \n"
                f"\n"
                f"Valor UF: ${self.parametros['valor_uf']:,.0f} | "
                f"Ingreso mínimo: ${self.parametros['ingreso_minimo']:,.0f} | "
                #f"Tope imponible: {self.parametros['tope_imponible_uf']} UF (${tope_imponible_pesos:,.2f}) | "
                f"Tope gratificación: ${tope_grat:,.0f} "
                #f"Tramos impuesto: {len(self.tramos_impuesto)}").replace(',', '.'
                )

    def _format_currency_sueldo(self, event):
        """Formatea el input de sueldo como moneda chilena"""
        self._format_currency_field(self.sueldo_liquido_var)

    def _format_currency_movilizacion(self, event):
        """Formatea el input de movilización como moneda chilena"""
        self._format_currency_field(self.movilizacion_var)

    def _format_currency_bono(self, event):
        """Formatea el input del bono como moneda chilena"""
        self._format_currency_field(self.bono_monto_var)

    def _format_currency_field(self, var: tk.StringVar):
        """Método genérico para formatear campos de moneda"""
        value = var.get().replace('.', '').replace(',', '')
        if value.isdigit() and value:
            formatted = f"{int(value):,}".replace(',', '.')
            var.set(formatted)

    # Mantener métodos existentes para compatibilidad
    def format_currency(self, event):
        """Formatea el input como moneda chilena (método legacy)"""
        self._format_currency_sueldo(event)

    def format_bono_currency(self, event):
        """Formatea el input del bono como moneda chilena (método legacy)"""
        self._format_currency_bono(event)

    # --- Gestión de Bonos ---
    def agregar_bono(self):
        """Agrega un bono a la lista"""
        nombre = self.bono_nombre_var.get().strip()
        monto_str = self.bono_monto_var.get().replace('.', '').replace(',', '')
        imponible = self.bono_imponible_var.get()
        
        if not nombre or not monto_str.isdigit():
            messagebox.showerror("Error", "Ingrese nombre y monto válido para el bono.")
            return
            
        monto = int(monto_str)
        if monto <= 0:
            messagebox.showerror("Error", "El monto del bono debe ser mayor a 0.")
            return
            
        self.bonos.append({"nombre": nombre, "monto": monto, "imponible": imponible})
        self.actualizar_lista_bonos()
        
        # Limpiar campos
        self._limpiar_campos_bono()

    def _limpiar_campos_bono(self):
        """Limpia los campos del formulario de bonos"""
        self.bono_nombre_var.set("")
        self.bono_monto_var.set("")
        self.bono_imponible_var.set(True)

    def eliminar_bono(self):
        """Elimina el bono seleccionado"""
        seleccion = self.bonos_listbox.curselection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un bono para eliminar.")
            return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar el bono seleccionado?"):
            idx = seleccion[0]
            del self.bonos[idx]
            self.actualizar_lista_bonos()

    def actualizar_lista_bonos(self):
        """Actualiza la lista visual de bonos"""
        self.bonos_listbox.delete(0, tk.END)
        for bono in self.bonos:
            tipo = "✅ Imponible" if bono["imponible"] else "❌ No Imponible"
            texto = f'{bono["nombre"]}: ${bono["monto"]:,.0f} ({tipo})'.replace(',', '.')
            self.bonos_listbox.insert(tk.END, texto)










    # --- Parámetros avanzados ---
    def abrir_parametros(self):
        """Abre la ventana de parámetros avanzados"""
        win = tk.Toplevel(self.root)
        win.title("Parámetros Avanzados")
        win.geometry("650x580+200+100")
        win.configure(bg='#f0f0f0')
        win.grab_set()
        win.resizable(False, False)

        self._configurar_ventana_parametros(win)

    def _configurar_ventana_parametros(self, win):
        """Configura la ventana de parámetros avanzados"""
        # Frame principal centrado
        main_frame = tk.Frame(win, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=30, pady=20)

        # Título
        tk.Label(main_frame, text="Configuración de Parámetros", font=('Arial', 15, 'bold'), 
                bg='#f0f0f0', fg='#2c3e50').pack(pady=(0, 20))

        # Frame para parámetros
        params_frame = tk.Frame(main_frame, bg='#f0f0f0')
        params_frame.pack(fill='x', pady=(0, 20))

        self._crear_campos_parametros(params_frame)

        # --- AGREGA LOS BOTONES AQUÍ ---
        self._crear_botones_parametros(main_frame, win)
        self._crear_separador(main_frame)
        self._crear_boton_tramos(main_frame)
        self._crear_parametros_calculados(main_frame)

    def _crear_campos_parametros(self, parent):
        """Crea los campos editables de parámetros"""
        labels_editables = [
            ("Ingreso mínimo ($):", "ingreso_minimo"),
            ("Valor UF ($):", "valor_uf"),
            ("Tope imponible (UF):", "tope_imponible_uf"),
            ("Tasa AFP (ej: 0.1049):", "tasa_afp"),
            ("Tasa Salud (ej: 0.07):", "tasa_salud"),
            ("Tasa Cesantía (ej: 0.006):", "tasa_cesant"),
            #("Factor gratificación (4.75):", "factor_gratificacion"),
            #("% Gratificación (0.25):", "porcentaje_gratificacion")
        ]

        self.param_vars = {}
        for i, (label, key) in enumerate(labels_editables):
            tk.Label(parent, text=label, font=('Arial', 10), bg='#f0f0f0').grid(
                row=i, column=0, sticky='e', padx=15, pady=8)
            var = tk.StringVar(value=str(self.parametros[key]))
            entry = tk.Entry(parent, textvariable=var, width=20, font=('Arial', 10))
            entry.grid(row=i, column=1, padx=15, pady=8)
            self.param_vars[key] = var

    def _crear_separador(self, parent):
        """Crea un separador visual"""
        separator = tk.Frame(parent, height=2, bg='#bdc3c7')
        separator.pack(fill='x', pady=15)

    def _crear_boton_tramos(self, parent):
        """Crea el botón para editar tramos de impuesto"""
        tk.Button(parent, text="Editar Tramos de Impuesto 2ª Categoría", 
                 command=self.abrir_tramos_impuesto, bg='#9b59b6', fg='white', 
                 font=('Arial', 11, 'bold'), relief='flat', padx=15, pady=8).pack(pady=10)

    def _crear_parametros_calculados(self, parent):
        """Crea la sección de parámetros calculados"""
        calc_frame = tk.Frame(parent, bg='#f0f0f0')
        calc_frame.pack(fill='x', pady=(10, 20))

        tk.Label(calc_frame, text="Parámetros Calculados:", 
                font=('Arial', 10, 'bold'), bg='#f0f0f0', fg='#7f8c8d').pack()

        self.tope_grat_label = tk.Label(calc_frame, text="", font=('Arial', 9), bg='#f0f0f0', fg='#7f8c8d')
        self.tope_grat_label.pack(pady=2)

        self.tope_afp_salud_label = tk.Label(calc_frame, text="", font=('Arial', 9), bg='#f0f0f0', fg='#7f8c8d')
        self.tope_afp_salud_label.pack(pady=2)
        
        self.tope_cesantia_label = tk.Label(calc_frame, text="", font=('Arial', 9), bg='#f0f0f0', fg='#7f8c8d')
        self.tope_cesantia_label.pack(pady=2)

        # Actualizar labels calculados
        self.actualizar_labels_calculados()

        # Bind para actualizar en tiempo real
        for var in self.param_vars.values():
            var.trace('w', lambda *args: self.actualizar_labels_calculados())

    def actualizar_labels_calculados(self):
        """Actualiza los labels de parámetros calculados en tiempo real"""
        try:
            ingreso_min = self._parse_currency(self.param_vars["ingreso_minimo"].get())
            valor_uf = self._parse_currency(self.param_vars["valor_uf"].get())
            tope_uf = float(self.param_vars["tope_imponible_uf"].get())
            factor_grat = self.parametros["factor_gratificacion"]
            
            tope_grat = factor_grat * ingreso_min / 12
            tope_afp_salud_pesos = tope_uf * valor_uf
            tope_cesantia_pesos = 131.8 * valor_uf
            
            self.tope_grat_label.config(text=f"Tope gratificación: ${tope_grat:,.0f}".replace(',', '.'))
            self.tope_afp_salud_label.config(text=f"Tope AFP/Salud: ${tope_afp_salud_pesos:,.0f}".replace(',', '.'))
            self.tope_cesantia_label.config(text=f"Tope Seguro Cesantía: ${tope_cesantia_pesos:,.0f}".replace(',', '.'))
        except (ValueError, KeyError):
            self.tope_grat_label.config(text="Tope gratificación: Error en cálculo")
            self.tope_afp_salud_label.config(text="Tope AFP/Salud: Error en cálculo")
            self.tope_cesantia_label.config(text="Tope Seguro Cesantía: Error en cálculo")

    def _parse_currency(self, value: str) -> float:
        """Convierte string de moneda a float"""
        return float(value.replace('.', '').replace(',', ''))

    def guardar_parametros(self, win):
        """Guarda los parámetros modificados permanentemente"""
        try:
            # Validar y guardar parámetros
            for key, var in self.param_vars.items():
                val_str = var.get().replace('.', '').replace(',', '')
                if key in ["tasa_afp", "tasa_salud", "tasa_cesant", "factor_gratificacion", "porcentaje_gratificacion", "tope_imponible_uf"]:
                    self.parametros[key] = float(var.get())
                else:
                    self.parametros[key] = int(val_str) if val_str.isdigit() else float(val_str)
            
            # Validar valores
            self._validar_parametros()
            
            # Guardar en archivo
            if self.guardar_configuracion():
                # Actualizar info en ventana principal
                self.info_label.config(text=self.get_info_parametros())
                # Actualizar visualización de AFP
                self.actualizar_interface_afp()
                messagebox.showinfo("Guardado", "¡Parámetros guardados correctamente!")
                win.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Revisa los valores ingresados: {e}")

    def _validar_parametros(self):
        """Valida que los parámetros sean correctos"""
        if self.parametros["ingreso_minimo"] <= 0:
            raise ValueError("El ingreso mínimo debe ser mayor a 0")
        if self.parametros["valor_uf"] <= 0:
            raise ValueError("El valor UF debe ser mayor a 0")
        if not (0 < self.parametros["tasa_afp"] < 1):
            raise ValueError("La tasa AFP debe estar entre 0 y 1")
        if not (0 < self.parametros["tasa_salud"] < 1):
            raise ValueError("La tasa de salud debe estar entre 0 y 1")

    # --- Tramos de impuesto ---
    def abrir_tramos_impuesto(self):
        """Abre la ventana de edición de tramos de impuesto"""
        tramos_win = tk.Toplevel(self.root)
        tramos_win.title("📊 Tramos de Impuesto 2ª Categoría")
        tramos_win.geometry("900x650+150+50")
        tramos_win.configure(bg='#f0f0f0')
        tramos_win.grab_set()

        self._configurar_ventana_tramos(tramos_win)

    def _configurar_ventana_tramos(self, win):
        """Configura la ventana de tramos de impuesto"""
        # Título
        tk.Label(win, text="Tramos de Impuesto de Segunda Categoría", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Frame principal
        main_frame = tk.Frame(win, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self._crear_treeview_tramos(main_frame)
        self._crear_botones_tramos(win)
        self._crear_botones_principales_tramos(win)

    def _crear_treeview_tramos(self, parent):
        """Crea el treeview para mostrar tramos"""
        columns = ('Desde', 'Hasta', 'Tasa (%)', 'Rebaja ($)')
        self.tramos_tree = ttk.Treeview(parent, columns=columns, show='headings', height=12)
        
        # Configurar columnas
        for col in columns:
            self.tramos_tree.heading(col, text=col + (' ($)' if col in ['Desde', 'Hasta', 'Rebaja ($)'] else ''))
        
        self.tramos_tree.column('Desde', width=150, anchor='e')
        self.tramos_tree.column('Hasta', width=150, anchor='e')
        self.tramos_tree.column('Tasa (%)', width=100, anchor='e')
        self.tramos_tree.column('Rebaja ($)', width=150, anchor='e')

        # Scrollbar para el treeview
        scrollbar_tramos = ttk.Scrollbar(parent, orient='vertical', command=self.tramos_tree.yview)
        self.tramos_tree.configure(yscrollcommand=scrollbar_tramos.set)

        self.tramos_tree.pack(side='left', fill='both', expand=True)
        scrollbar_tramos.pack(side='right', fill='y')

        # Cargar tramos actuales
        self.actualizar_tramos_tree()

    def _crear_botones_tramos(self, win):
        """Crea los botones para gestionar tramos"""
        btn_tramos_frame = tk.Frame(win, bg='#f0f0f0')
        btn_tramos_frame.pack(pady=15)

        botones = [
            ("➕ Agregar Tramo", self.agregar_tramo, '#27ae60'),
            ("✏️ Editar Tramo", self.editar_tramo, '#3498db'),
            ("🗑️ Eliminar Tramo", self.eliminar_tramo, '#e74c3c')
        ]

        for texto, comando, color in botones:
            tk.Button(btn_tramos_frame, text=texto, command=comando, 
                     bg=color, fg='white', font=('Arial', 10, 'bold'), 
                     relief='flat', padx=15, pady=8).pack(side='left', padx=5)

    def _crear_botones_principales_tramos(self, win):
        """Crea los botones principales de la ventana de tramos"""
        btn_main_frame = tk.Frame(win, bg='#f0f0f0')
        btn_main_frame.pack(pady=15)

        tk.Button(btn_main_frame, text="💾 Guardar Tramos", command=lambda: self.guardar_tramos(win), 
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=10).pack(side='left', padx=10)
        
        tk.Button(btn_main_frame, text="❌ Cerrar", command=win.destroy, 
                 bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'), relief='flat', padx=20, pady=10).pack(side='left', padx=10)

    def actualizar_tramos_tree(self):
        """Actualiza el treeview con los tramos actuales"""
        # Limpiar treeview
        for item in self.tramos_tree.get_children():
            self.tramos_tree.delete(item)
        
        # Agregar tramos
        for tramo in self.tramos_impuesto:
            hasta_texto = f"{tramo['hasta']:,.0f}".replace(',', '.') if tramo['hasta'] < 999999999999 else "∞"
            self.tramos_tree.insert('', 'end', values=(
                f"{tramo['desde']:,.0f}".replace(',', '.'),
                hasta_texto,
                f"{tramo['tasa']*100:.2f}%",
                f"{tramo['rebaja']:,.0f}".replace(',', '.')
            ))

    def agregar_tramo(self):
        """Abre ventana para agregar nuevo tramo"""
        self.abrir_editor_tramo("Agregar Tramo", {})

    def editar_tramo(self):
        """Abre ventana para editar tramo seleccionado"""
        seleccion = self.tramos_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un tramo para editar.")
            return
        
        idx = self.tramos_tree.index(seleccion[0])
        tramo = self.tramos_impuesto[idx]
        self.abrir_editor_tramo("Editar Tramo", tramo, idx)

    def eliminar_tramo(self):
        """Elimina el tramo seleccionado"""
        seleccion = self.tramos_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un tramo para eliminar.")
            return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar el tramo seleccionado?"):
            idx = self.tramos_tree.index(seleccion[0])
            del self.tramos_impuesto[idx]
            self.actualizar_tramos_tree()

    def abrir_editor_tramo(self, titulo: str, tramo: Dict[str, Any], idx: Optional[int] = None):
        """Abre ventana para editar/agregar tramo"""
        editor_win = tk.Toplevel(self.root)
        editor_win.title(titulo)
        editor_win.geometry("450x350+300+200")
        editor_win.configure(bg='#f0f0f0')
        editor_win.grab_set()
        editor_win.resizable(False, False)

        self._configurar_editor_tramo(editor_win, titulo, tramo, idx)

    def _configurar_editor_tramo(self, win, titulo: str, tramo: Dict[str, Any], idx: Optional[int]):
        """Configura la ventana del editor de tramos"""
        # Frame principal centrado
        main_frame = tk.Frame(win, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=30, pady=20)

        # Título
        tk.Label(main_frame, text=titulo, font=('Arial', 12, 'bold'), 
                bg='#f0f0f0', fg='#2c3e50').pack(pady=(0, 20))

        # Frame para campos
        campos_frame = tk.Frame(main_frame, bg='#f0f0f0')
        campos_frame.pack(pady=10)

        # Variables
        desde_var = tk.StringVar(value=str(tramo.get('desde', '')))
        hasta_var = tk.StringVar(value=str(tramo.get('hasta', '')) if tramo.get('hasta', 0) < 999999999999 else '')
        tasa_var = tk.StringVar(value=str(tramo.get('tasa', '')))
        rebaja_var = tk.StringVar(value=str(tramo.get('rebaja', '')))
        infinito_var = tk.BooleanVar(value=tramo.get('hasta', 0) >= 999999999999)

        # Crear campos
        hasta_entry = self._crear_campos_editor_tramo(campos_frame, desde_var, hasta_var, tasa_var, rebaja_var, infinito_var)
        
        # Crear botones
        self._crear_botones_editor_tramo(main_frame, win, desde_var, hasta_var, tasa_var, rebaja_var, infinito_var, idx)

    def _crear_campos_editor_tramo(self, parent, desde_var, hasta_var, tasa_var, rebaja_var, infinito_var):
        """Crea los campos del editor de tramos"""
        # Campos
        tk.Label(parent, text="Desde ($):", bg='#f0f0f0').grid(row=0, column=0, sticky='e', padx=10, pady=8)
        tk.Entry(parent, textvariable=desde_var, width=20).grid(row=0, column=1, padx=10, pady=8)

        tk.Label(parent, text="Hasta ($):", bg='#f0f0f0').grid(row=1, column=0, sticky='e', padx=10, pady=8)
        hasta_entry = tk.Entry(parent, textvariable=hasta_var, width=20)
        hasta_entry.grid(row=1, column=1, padx=10, pady=8)

        def toggle_infinito():
            if infinito_var.get():
                hasta_entry.config(state='disabled')
                hasta_var.set('')
            else:
                hasta_entry.config(state='normal')

        tk.Checkbutton(parent, text="Hasta infinito", variable=infinito_var, 
                      command=toggle_infinito, bg='#f0f0f0').grid(row=2, column=0, columnspan=2, pady=5)

        tk.Label(parent, text="Tasa (ej: 0.04):", bg='#f0f0f0').grid(row=3, column=0, sticky='e', padx=10, pady=8)
        tk.Entry(parent, textvariable=tasa_var, width=20).grid(row=3, column=1, padx=10, pady=8)

        tk.Label(parent, text="Rebaja ($):", bg='#f0f0f0').grid(row=4, column=0, sticky='e', padx=10, pady=8)
        tk.Entry(parent, textvariable=rebaja_var, width=20).grid(row=4, column=1, padx=10, pady=8)

        # Configurar estado inicial
        toggle_infinito()
        
        return hasta_entry

    def _crear_botones_editor_tramo(self, parent, win, desde_var, hasta_var, tasa_var, rebaja_var, infinito_var, idx):
        """Crea los botones del editor de tramos"""
        btn_frame = tk.Frame(parent, bg='#f0f0f0')
        btn_frame.pack(pady=20)

        def guardar_tramo():
            try:
                desde = float(desde_var.get().replace('.', '').replace(',', ''))
                hasta = 999999999999 if infinito_var.get() else float(hasta_var.get().replace('.', '').replace(',', ''))
                tasa = float(tasa_var.get())
                rebaja = float(rebaja_var.get().replace('.', '').replace(',', ''))

                # Validaciones
                if desde < 0 or (not infinito_var.get() and hasta <= desde):
                    raise ValueError("Los valores de rango son inválidos")
                if not (0 <= tasa <= 1):
                    raise ValueError("La tasa debe estar entre 0 y 1")
                if rebaja < 0:
                    raise ValueError("La rebaja no puede ser negativa")

                nuevo_tramo = {
                    "desde": desde,
                    "hasta": hasta,
                    "tasa": tasa,
                    "rebaja": rebaja
                }

                if idx is not None:  # Editar
                    self.tramos_impuesto[idx] = nuevo_tramo
                else:  # Agregar
                    self.tramos_impuesto.append(nuevo_tramo)

                # Ordenar tramos por valor "desde"
                self.tramos_impuesto.sort(key=lambda x: x['desde'])
                
                self.actualizar_tramos_tree()
                win.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Error en los datos: {e}")

        tk.Button(btn_frame, text="💾 Guardar", command=guardar_tramo, 
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=win.destroy, 
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'), relief='flat', padx=20, pady=8).pack(side='left', padx=10)

    def guardar_tramos(self, win):
        """Guarda los tramos y cierra la ventana"""
        if self.guardar_configuracion():
            messagebox.showinfo("Guardado", "¡Tramos de impuesto guardados correctamente!")
            self.info_label.config(text=self.get_info_parametros())
            win.destroy()

    #-----------------------------------------------------------
    #                       Cálculo Mejorado
    #-----------------------------------------------------------
    def get_tasa_afp(self) -> float:
        """Obtiene la tasa de AFP configurada en parámetros"""
        return self.parametros["tasa_afp"]

    def impuesto_unico(self, imponible: float) -> float:
        """
        Calcula impuesto único según tramos configurados
        Tramos SII agosto 2025 (pesos mensuales)
        """
        # Validación de entrada
        if imponible <= 0:
            return 0.0
        
        if not self.tramos_impuesto:
            print("Error: No hay tramos de impuesto configurados")
            return 0.0
            
        # Buscar tramo aplicable usando la estructura de tramos de la app
        for tramo in self.tramos_impuesto:
            if tramo['desde'] <= imponible <= tramo['hasta']:
                impuesto = imponible * tramo['tasa'] - tramo['rebaja']
                return max(impuesto, 0.0)
        
        # Si no encuentra tramo exacto, usar el último tramo para montos altos
        tramos_ordenados = sorted(self.tramos_impuesto, key=lambda x: x['desde'])
        if imponible > tramos_ordenados[-1]['desde']:
            tramo_aplicable = tramos_ordenados[-1]
            impuesto = imponible * tramo_aplicable['tasa'] - tramo_aplicable['rebaja']
            return max(impuesto, 0.0)
        
        return 0.0

    def _calcular_sueldo_base_hibrido(self, sueldo_liquido_deseado: int, movilizacion: int) -> Dict[str, Any]:
        """
        Método basado en calcular_base.py - Calcula el sueldo base necesario para alcanzar un sueldo líquido deseado
        usando búsqueda binaria con precisión adaptativa
        """
        try:
            # ----------------------------------------------------------
            # Parámetros - adaptados de la configuración de la app
            # ----------------------------------------------------------
            ingreso_minimo = self.parametros["ingreso_minimo"]
            uf = self.parametros["valor_uf"]
            max_imponible_afp_salud = self.parametros["tope_imponible_uf"]  # Tope imponible AFP y salud
            max_imponible_seguro_cesantia = 131.8  # Tope imponible Seguro Cesantía
            
            # Tasas y topes
            tasa_afp = self.get_tasa_afp()
            tasa_cesantia_trabajador = self.parametros["tasa_cesant"]
            
            # Conversión tope imponible (UF) a pesos
            tope_imponible_pesos_afp_salud = max_imponible_afp_salud * uf
            tope_imponible_seguro_cesantia_pesos = max_imponible_seguro_cesantia * uf
            
            # Suma de bonos
            total_bonos_imponibles = sum(b["monto"] for b in self.bonos if b.get("imponible", False))
            total_bonos_no_imponibles = sum(b["monto"] for b in self.bonos if not b.get("imponible", False))
            
            precision = max(10, min(1000, sueldo_liquido_deseado * 0.001))

            # Función para estimar el líquido desde un sueldo base
            def estimar_liquido(sueldo_base):
                tope_gratificacion_mensual = self.parametros["factor_gratificacion"] * ingreso_minimo / 12
                gratificacion = min(self.parametros["porcentaje_gratificacion"] * sueldo_base, tope_gratificacion_mensual)

                imponible = sueldo_base + gratificacion + total_bonos_imponibles

                # Aplicar topes según calcular_base.py
                cotiz_prev = min(imponible * tasa_afp, tope_imponible_pesos_afp_salud * tasa_afp)
                
                # Calcular cotización de salud según tipo seleccionado con tope correcto
                if self.tipo_salud_var.get() == "fonasa":
                    cotiz_salud = min(imponible * self.parametros["tasa_salud"], tope_imponible_pesos_afp_salud * self.parametros["tasa_salud"])
                else:
                    cotiz_salud, _ = self.get_cotizacion_salud(imponible)
                
                cesantia = min(imponible * tasa_cesantia_trabajador, tope_imponible_seguro_cesantia_pesos * tasa_cesantia_trabajador)

                base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
                impuesto2cat = self.impuesto_unico(base_tributable)

                total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
                total_haberes = imponible + movilizacion + total_bonos_no_imponibles
                return total_haberes - total_descuentos

            # Rango inicial dinámico
            sueldo_min = 0
            sueldo_max = sueldo_liquido_deseado
            while estimar_liquido(sueldo_max) < sueldo_liquido_deseado:
                sueldo_max *= 2  # Duplicar hasta encontrar un rango que contenga el sueldo deseado
            
            # Búsqueda binaria
            iteraciones = 0
            max_iterations = 50
            
            while sueldo_max - sueldo_min > precision and iteraciones < max_iterations:
                sueldo_base = (sueldo_min + sueldo_max) / 2
                sueldo_liquido_calculado = estimar_liquido(sueldo_base)
                
                if sueldo_liquido_calculado < sueldo_liquido_deseado:
                    sueldo_min = sueldo_base
                else:
                    sueldo_max = sueldo_base
                
                iteraciones += 1
            
            sueldo_base = round(sueldo_base)
            
            # Recalculamos todo con el sueldo base encontrado
            tope_grat_mensual = self.parametros["factor_gratificacion"] * ingreso_minimo / 12
            gratificacion = min(self.parametros["porcentaje_gratificacion"] * sueldo_base, tope_grat_mensual)
            imponible = sueldo_base + gratificacion + total_bonos_imponibles
            
            # Aplicar topes correctamente según calcular_base.py
            cotiz_prev = min(imponible * tasa_afp, tope_imponible_pesos_afp_salud * tasa_afp)
            
            # Calcular cotización de salud con tope correcto
            if self.tipo_salud_var.get() == "fonasa":
                cotiz_salud = min(imponible * self.parametros["tasa_salud"], tope_imponible_pesos_afp_salud * self.parametros["tasa_salud"])
                descripcion_salud = f"Fonasa ({self.parametros['tasa_salud']*100:.1f}%)"
            else:
                cotiz_salud, descripcion_salud = self.get_cotizacion_salud(imponible)
            
            cesantia = min(imponible * tasa_cesantia_trabajador, tope_imponible_seguro_cesantia_pesos * tasa_cesantia_trabajador)
            
            base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
            impuesto2cat = self.impuesto_unico(base_tributable)
            total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
            total_haberes = imponible + movilizacion + total_bonos_no_imponibles
            sueldo_liquido = total_haberes - total_descuentos
            
            # Detectar si se alcanzaron los topes
            tope_afp_salud_alcanzado = imponible > tope_imponible_pesos_afp_salud
            tope_cesantia_alcanzado = imponible > tope_imponible_seguro_cesantia_pesos
            
            return {
                'deseado': sueldo_liquido_deseado,
                'base': sueldo_base,
                'grat': gratificacion,
                'imponible': imponible,
                'mov': movilizacion,
                'afp': cotiz_prev,
                'salud': cotiz_salud,
                'cesant': cesantia,
                'imp': impuesto2cat,
                'base_trib': base_tributable,
                'desc': total_descuentos,
                'hab': total_haberes,
                'liquido': sueldo_liquido,
                'bonos_imp': total_bonos_imponibles,
                'bonos_noimp': total_bonos_no_imponibles,
                'tope_imp_afp_salud': tope_imponible_pesos_afp_salud,
                'tope_imp_cesantia': tope_imponible_seguro_cesantia_pesos,
                'tope_afp_salud_alcanzado': tope_afp_salud_alcanzado,
                'tope_cesantia_alcanzado': tope_cesantia_alcanzado,
                'diferencia': sueldo_liquido - sueldo_liquido_deseado,
                'iteraciones': iteraciones,
                'descripcion_salud': descripcion_salud
            }
            
        except Exception as e:
            print(f"Error en _calcular_sueldo_base_hibrido: {e}")
            return None

    def calcular(self):
        """Función principal de cálculo con validaciones mejoradas"""
        try:
            # Validar entrada de sueldo líquido
            sueldo_str = self.sueldo_liquido_var.get().replace('.', '').replace(',', '').strip()
            if not sueldo_str or not sueldo_str.isdigit():
                messagebox.showerror("Error", "Por favor ingrese un sueldo líquido válido (solo números)")
                return
                
            sueldo_liquido_deseado = int(sueldo_str)
            
            # Validar rango del sueldo
            if sueldo_liquido_deseado <= 0:
                messagebox.showerror("Error", "El sueldo debe ser mayor a 0")
                return
            
            if sueldo_liquido_deseado > 100_000_000:  # Límite razonable
                messagebox.showerror("Error", "El sueldo ingresado excede el límite máximo permitido")
                return

            # Validar entrada de movilización
            movilizacion_str = self.movilizacion_var.get().replace('.', '').replace(',', '').strip()
            if movilizacion_str and not movilizacion_str.isdigit():
                messagebox.showerror("Error", "La movilización debe ser un número válido")
                return
            
            movilizacion = int(movilizacion_str) if movilizacion_str.isdigit() else 0
            
            # Validar que existan tramos de impuestos
            if not self.tramos_impuesto:
                messagebox.showerror("Error", "No se han configurado los tramos de impuesto")
                return
            

            print(f"Debug: Calculando para sueldo líquido: {sueldo_liquido_deseado}")
            print(f"Debug: Movilización: {movilizacion}")
            print(f"Debug: Bonos imponibles: {sum(b['monto'] for b in self.bonos if b.get('imponible', False))}")
            print(f"Debug: Tramos configurados: {len(self.tramos_impuesto)}")


            # Realizar cálculo
            resultado = self._calcular_sueldo_base_hibrido(sueldo_liquido_deseado, movilizacion)
            
            if resultado is None:
                print("❌ Error detallado: resultado es None")
                # Intentar un cálculo simple para debug
                try:
                    test_impuesto = self.impuesto_unico(1000000)
                    print(f"Test impuesto para 1M: {test_impuesto}")
                except Exception as test_e:
                    print(f"Error en test de impuesto: {test_e}")
                
                messagebox.showerror("Error Detallado", 
                                    "No se pudo calcular el sueldo base.\n\n"
                                    "Revisa la consola para más detalles.\n"
                                    "Verifica que los tramos de impuesto estén bien configurados.")
                return
                        
            # Mostrar resultados
            self.mostrar_resultados_popup(**resultado)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Error en los datos ingresados: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado en el cálculo: {str(e)}")

    def _calcular_valores_intermedios_seguro(
            self, sueldo_base: float, tope_grat_mensual: float, 
            total_bonos_imponibles: int, tope_imponible: float,
            tasa_afp: float, tasa_salud: float, tasa_cesant: float,
            movilizacion: int, total_bonos_no_imponibles: int) -> Dict[str, float]:
        """Calcula valores intermedios con validaciones y manejo de errores"""
        try:
            # Validar entradas
            if sueldo_base < 0:
                return None
            
            # Gratificación legal con validación
            porcentaje_grat = self.parametros.get("porcentaje_gratificacion", 0.25)
            gratificacion = min(porcentaje_grat * sueldo_base, tope_grat_mensual)
            gratificacion = max(0, gratificacion)  # No puede ser negativa
            
            # Total imponible con límite
            imponible = sueldo_base + gratificacion + total_bonos_imponibles
            imponible = min(imponible, tope_imponible)  # Aplicar tope
            imponible = max(0, imponible)  # No puede ser negativo
            
            # Descuentos con validaciones
            cotiz_prev = max(0, imponible * tasa_afp)
            cotiz_salud = max(0, imponible * tasa_salud)
            cesant = max(0, imponible * tasa_cesant)
            
            # Base tributable
            base_tributable = max(0, imponible - (cotiz_prev + cotiz_salud + cesant))
            
            # Impuesto con validación
            try:
                if base_tributable > 0:
                    impuesto2cat = self.impuesto_unico(base_tributable)
                    if impuesto2cat is None or impuesto2cat < 0:
                        impuesto2cat = 0.0
                else:
                    impuesto2cat = 0.0
            except Exception as e:
                print(f"Error calculando impuesto para base {base_tributable}: {e}")
                impuesto2cat = 0.0
            
            # Totales
            total_descuentos = cotiz_prev + cotiz_salud + cesant + impuesto2cat
            total_haberes = imponible + movilizacion + total_bonos_no_imponibles
            sueldo_liquido = total_haberes - total_descuentos
            
            # Validar resultado final
            if sueldo_liquido < 0:
                sueldo_liquido = 0
            
            return {
                'gratificacion': round(gratificacion, 2),
                'imponible': round(imponible, 2),
                'cotiz_prev': round(cotiz_prev, 2),
                'cotiz_salud': round(cotiz_salud, 2),
                'cesant': round(cesant, 2),
                'base_tributable': round(base_tributable, 2),
                'impuesto2cat': round(impuesto2cat, 2),
                'total_descuentos': round(total_descuentos, 2),
                'total_haberes': round(total_haberes, 2),
                'sueldo_liquido': round(sueldo_liquido, 2)
            }
            
        except Exception as e:
            print(f"Error en _calcular_valores_intermedios_seguro: {e}")
            return None

    def mostrar_resultados_popup(self, deseado: int, base: int, grat: float, imponible: float, 
                                mov: int, afp: float, salud: float, cesant: float, imp: float, 
                                base_trib: float, desc: float, hab: float, liquido: float, 
                                bonos_imp: int, bonos_noimp: int, tope_imp_afp_salud: float,
                                diferencia: float = 0, iteraciones: int = 0, **kwargs):
        """Muestra los resultados en una ventana emergente con información adicional"""
        
        # Crear ventana de resultados
        result_win = tk.Toplevel(self.root)
        result_win.title("📊 Resultados del Cálculo")
        result_win.geometry("950x800+100+50")
        result_win.configure(bg='#f0f0f0')
        result_win.grab_set()
        
        # Centrar ventana
        result_win.transient(self.root)

        self._configurar_ventana_resultados_mejorada(result_win, deseado, base, grat, imponible, 
                                                    mov, afp, salud, cesant, imp, base_trib, 
                                                    desc, hab, liquido, bonos_imp, bonos_noimp, 
                                                    tope_imp_afp_salud, diferencia, iteraciones)

    def _configurar_ventana_resultados_mejorada(self, win, deseado, base, grat, imponible, mov, afp, 
                                            salud, cesant, imp, base_trib, desc, hab, liquido, 
                                            bonos_imp, bonos_noimp, tope_imp_afp_salud, diferencia, iteraciones):
        """Configura la ventana de resultados mejorada"""
        # Título con color basado en precisión
        color_titulo = '#27ae60' if abs(diferencia) <= 1000 else '#e67e22' if abs(diferencia) <= 5000 else '#e74c3c'
        
        title_frame = tk.Frame(win, bg=color_titulo, height=60)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="📊 RESULTADOS DEL CÁLCULO DE SUELDO", 
                font=('Arial', 16, 'bold'), fg='white', bg=color_titulo).pack(expand=True)

        # Frame principal para resultados
        main_frame = tk.Frame(win, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Generar texto de resultados
        resultado = self._generar_texto_resultados_mejorado(deseado, base, grat, imponible, mov, afp, 
                                                            salud, cesant, imp, base_trib, desc, hab, 
                                                            liquido, bonos_imp, bonos_noimp, tope_imp_afp_salud, 
                                                            diferencia, iteraciones)

        # Text widget con scrollbar
        self._crear_text_widget_resultados(main_frame, resultado)
        
        # Botones
        self._crear_botones_resultados(win, resultado)

    def _generar_texto_resultados_mejorado(self, deseado, base, grat, imponible, mov, afp, salud, 
                                        cesant, imp, base_trib, desc, hab, liquido, bonos_imp, 
                                        bonos_noimp, tope_imp_afp_salud, diferencia, iteraciones, **kwargs) -> str:
        """Genera el texto formateado de los resultados con información adicional"""
        def format_number(num):
            if abs(num - round(num)) < 0.01:
                return f"{num:,.0f}".replace(',', '.')
            else:
                return f"{num:,.2f}".replace(',', '.') 

        # Análisis de precisión
        precision_text = ""
        if abs(diferencia) <= 100:
            precision_text = "🎯 EXCELENTE"
        elif abs(diferencia) <= 1000:
            precision_text = "✅ BUENA"
        elif abs(diferencia) <= 5000:
            precision_text = "⚠️  ACEPTABLE"
        else:
            precision_text = "❌ REVISAR"

        # Obtener información adicional de kwargs
        descripcion_salud = kwargs.get('descripcion_salud', 'Salud')
        tope_imp_cesantia = kwargs.get('tope_imp_cesantia', 0)
        tope_afp_salud_alcanzado = kwargs.get('tope_afp_salud_alcanzado', False)
        tope_cesantia_alcanzado = kwargs.get('tope_cesantia_alcanzado', False)

        # Crear texto de alertas de topes
        alertas_topes = ""
        if tope_afp_salud_alcanzado:
            alertas_topes += "⚠️  Se alcanzó el tope imponible AFP/Salud\n"
        if tope_cesantia_alcanzado:
            alertas_topes += "⚠️  Se alcanzó el tope imponible Seguro Cesantía\n"

        return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CÁLCULO DE SUELDO BASE                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 OBJETIVO Y RESULTADO
Sueldo líquido deseado:      ${format_number(deseado)}
Sueldo líquido calculado:    ${format_number(liquido)}
Diferencia:                  ${format_number(diferencia):>15} ({precision_text})

💰 RESULTADO PRINCIPAL
Sueldo base necesario:       ${format_number(base)}

📊 DETALLE DE HABERES
├─ Sueldo base:              ${format_number(base):>15}
├─ Gratificación legal:      ${format_number(grat):>15}
├─ Bonos imponibles:         ${format_number(bonos_imp):>15}
├─ Total Imponible:          ${format_number(imponible):>15}
├─ Movilización:             ${format_number(mov):>15}
├─ Bonos no imponibles:      ${format_number(bonos_noimp):>15}
└─ TOTAL HABERES:            ${format_number(hab):>15}

📉 DETALLE DE DESCUENTOS
├─ AFP ({self.parametros['tasa_afp']*100:.2f}%):                ${format_number(afp):>15}
├─ {descripcion_salud}:      ${format_number(salud):>15}
├─ Cesantía ({self.parametros['tasa_cesant']*100:.2f}%):        ${format_number(cesant):>15}
├─ Impuesto 2ª Cat.:                                            ${format_number(imp):>15}
└─ TOTAL DESCUENTOS:                                            ${format_number(desc):>15}

📋 INFORMACIÓN ADICIONAL
├─ Base tributable:          ${format_number(base_trib):>15}
├─ Tope gratificación:       ${format_number(self.parametros['factor_gratificacion'] * self.parametros['ingreso_minimo'] / 12):>15}
├─ Ingreso mínimo:           ${format_number(self.parametros['ingreso_minimo']):>15}
├─ Valor UF:                 ${format_number(self.parametros['valor_uf']):>15}
├─ Tope AFP/Salud:           ${format_number(tope_imp_afp_salud):>15} ({self.parametros['tope_imponible_uf']} UF)
├─ Tope Seguro Cesantía:     ${format_number(tope_imp_cesantia):>15} (131.8 UF)
├─ Bonos agregados:          {len(self.bonos):>15} bonos
├─ Tramos impuesto:          {len(self.tramos_impuesto):>15} tramos
└─ Iteraciones cálculo:      {iteraciones:>15}

⚡ TASAS APLICADAS
├─ AFP configurada:          {self.parametros['tasa_afp']*100:.2f}%
├─ Sistema salud:            {descripcion_salud}
├─ Tasa total descuentos:    {(self.parametros['tasa_afp'] + self.parametros['tasa_salud'] + self.parametros['tasa_cesant'])*100:.2f}%
└─ Tasa impuesto efectiva:   {(imp/base_trib*100) if base_trib > 0 else 0:.2f}%

{alertas_topes if alertas_topes else ""}--- INFORMACIÓN TÉCNICA ---
Valor UF utilizado: ${self.parametros['valor_uf']:,.0f}
Tope AFP/Salud: {self.parametros['tope_imponible_uf']} UF = ${tope_imp_afp_salud:,.0f}
Tope Cesantía: 131.8 UF = ${tope_imp_cesantia:,.0f}
{alertas_topes}
    """

    def _crear_text_widget_resultados(self, parent, resultado: str):
        """Crea el widget de texto para mostrar resultados"""
        text_frame = tk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        result_text = tk.Text(text_frame, font=('Courier', 10), bg='white', fg='#2c3e50', 
                            wrap='word', relief='solid', borderwidth=1)
        scrollbar = tk.Scrollbar(text_frame, orient='vertical', command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)

        result_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        result_text.insert(1.0, resultado)
        result_text.config(state='disabled')  # Solo lectura

    def _crear_botones_resultados(self, win, resultado: str):
        """Crea los botones de la ventana de resultados"""
        btn_frame = tk.Frame(win, bg='#f0f0f0')
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="📋 Copiar al Portapapeles", 
                command=lambda: self.copiar_resultados(resultado), 
                bg='#3498db', fg='white', font=('Arial', 11, 'bold'), 
                relief='flat', padx=20, pady=10).pack(side='left', padx=10)

        tk.Button(btn_frame, text="🔄 Nuevo Cálculo", 
                command=lambda: [win.destroy(), self.sueldo_liquido_var.set("")],
                bg='#f39c12', fg='white', font=('Arial', 11, 'bold'),
                relief='flat', padx=20, pady=10).pack(side='left', padx=10)

        tk.Button(btn_frame, text="✅ Cerrar", command=win.destroy,
                bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'),
                relief='flat', padx=20, pady=10).pack(side='left', padx=10)

    def copiar_resultados(self, resultado: str):
        """Copia los resultados al portapapeles"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(resultado)
            messagebox.showinfo("✅ Copiado", "¡Resultados copiados al portapapeles!")
        except Exception as e:
            messagebox.showerror("Error", f"Error al copiar: {e}")

    def actualizar_interface_afp(self):
        """Actualiza la visualización de la tasa AFP en la interfaz"""
        if hasattr(self, 'afp_label'):
            self.afp_label.config(text=f"{self.parametros['tasa_afp']*100:.2f}%")
        
        # Actualizar también el texto de Fonasa si cambió la tasa de salud
        if hasattr(self, 'fonasa_check'):
            self.fonasa_check.config(text=f"Fonasa ({self.parametros['tasa_salud']*100:.1f}%)")
        
        # Actualizar valor en pesos de Isapre si cambió el valor UF
        self._actualizar_valor_isapre_pesos()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraSueldos(root)
    root.mainloop()