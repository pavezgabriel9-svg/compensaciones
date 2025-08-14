#----
#    Importaciones
#----
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from typing import Dict, List, Any, Optional

#----
#    Creación de Interfaz de Usuario
#----

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

        # Tramos de impuesto por defecto - CORREGIDO
        self.tramos_default = [
            {"desde": 0,          "hasta": 926734.50,  "tasa": 0.00, "rebaja":       0.0},
            {"desde": 926734.51,  "hasta": 2059410.00, "tasa": 0.04, "rebaja":   37069.38},
            {"desde": 2059410.01, "hasta": 3432350.00, "tasa": 0.08, "rebaja":  119445.78},
            {"desde": 3432350.01, "hasta": 4805290.00, "tasa": 0.135,"rebaja":  308225.03},
            {"desde": 4805290.01, "hasta": 6178230.00, "tasa": 0.23, "rebaja":  764727.58},
            {"desde": 6178230.01, "hasta": 8237640.00, "tasa": 0.304,"rebaja": 1221916.60},
            {"desde": 8237640.01, "hasta": 21280570.00,"tasa": 0.35, "rebaja": 1600848.04},
            #  ∞  => usamos float('inf') para que todos los montos grandes entren aquí
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
            test_impuesto = self.impuesto_unico(1000000)  # 1 millón de prueba
            if test_impuesto is None:
                raise ValueError("Error en cálculo de impuestos de prueba")
            
            print("✅ Configuración inicial validada correctamente")
            
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
        self.afp_var = tk.StringVar(value="AFP Uno (10.49%)")
        self.salud_var = tk.StringVar(value="Fonasa (7%)")
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
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Calculadora de Sueldos", 
                              font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(expand=True, pady=10)

    def _crear_boton_calcular(self, parent):
        """Crea el botón de calcular"""
        calc_button = tk.Button(parent, text="Calcular Sueldo Base", 
                               command=self.calcular, font=('Arial', 13, 'bold'),
                               bg='#3498db', fg='white', relief='flat', padx=10, pady=10)
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
        tk.Label(parent, text="Sueldo Líquido Deseado ($):", 
                font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        sueldo_entry = tk.Entry(parent, textvariable=self.sueldo_liquido_var, 
                               font=('Arial', 12), width=13)
        sueldo_entry.grid(row=0, column=1, padx=5, pady=5)
        sueldo_entry.bind('<KeyRelease>', self._format_currency_sueldo)

    def _crear_campo_afp(self, parent):
        """Crea el campo de AFP"""
        tk.Label(parent, text="AFP:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=1, column=0, sticky='e', padx=5, pady=5)
        afp_combo = ttk.Combobox(parent, textvariable=self.afp_var, width=18, state='readonly')
        afp_combo['values'] = (
            'AFP Uno (10.49%)', 'Cuprum (10.44%)', 'Habitat (10.77%)',
            'Planvital (10.16%)', 'ProVida (10.55%)', 'Capital (11.44%)', 'Modelo (10.58%)'
        )
        afp_combo.grid(row=1, column=1, padx=5, pady=5)

    def _crear_campo_salud(self, parent):
        """Crea el campo de sistema de salud"""
        tk.Label(parent, text="Salud:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=2, column=0, sticky='e', padx=5, pady=5)
        salud_combo = ttk.Combobox(parent, textvariable=self.salud_var, width=18, state='readonly')
        salud_combo['values'] = ('Fonasa (7%)', 'Isapre (7% + plan)')
        salud_combo.grid(row=2, column=1, padx=5, pady=5)

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
        tope_grat = self.parametros["factor_gratificacion"] * self.parametros["ingreso_minimo"] / 12
        
        ancho = 100
        titulo = "Valores Utilizados".center(ancho)

        return (f"{titulo} \n"
                f"\n"
                f"Valor UF: ${self.parametros['valor_uf']:,.0f} | "
                f"Ingreso mínimo: ${self.parametros['ingreso_minimo']:,.0f} | "
                f"Tope gratificación: ${tope_grat:,.0f} "
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

        self.tope_imp_label = tk.Label(calc_frame, text="", font=('Arial', 9), bg='#f0f0f0', fg='#7f8c8d')
        self.tope_imp_label.pack(pady=2)

        # Actualizar labels calculados
        self.actualizar_labels_calculados()

        # Bind para actualizar en tiempo real
        for var in self.param_vars.values():
            var.trace('w', lambda *args: self.actualizar_labels_calculados())

    def _crear_botones_parametros(self, parent, win):
        """Crea los botones de la ventana de parámetros"""
        btn_frame = tk.Frame(parent, bg='#f0f0f0')
        btn_frame.pack(pady=15)

        # BOTÓN PRINCIPAL: Guardar y Aplicar (más prominente)
        tk.Button(btn_frame, text="Guardar y Aplicar", command=lambda: self.guardar_parametros(win), 
                 bg='#27ae60', fg='white', font=('Arial', 12, 'bold'), relief='flat', padx=25, pady=12).pack(side='left', padx=8)

    def actualizar_labels_calculados(self):
        """Actualiza los labels de parámetros calculados en tiempo real"""
        try:
            ingreso_min = self._parse_currency(self.param_vars["ingreso_minimo"].get())
            valor_uf = self._parse_currency(self.param_vars["valor_uf"].get())
            factor_grat = self.parametros["factor_gratificacion"]
            tope_grat = factor_grat * ingreso_min / 12
            
            self.tope_grat_label.config(text=f"Tope gratificación: ${tope_grat:,.0f}".replace(',', '.'))
        except (ValueError, KeyError):
            self.tope_grat_label.config(text="Tope gratificación: Error en cálculo")
            self.tope_imp_label.config(text="Tope imponible: Error en cálculo")

    def _parse_currency(self, value: str) -> float:
        """Convierte string de moneda a float"""
        return float(value.replace('.', '').replace(',', ''))

    def _validar_parametros_temp(self, parametros_temp):
        """Valida que los parámetros temporales sean correctos"""
        if parametros_temp["ingreso_minimo"] <= 0:
            raise ValueError("El ingreso mínimo debe ser mayor a 0")
        if parametros_temp["valor_uf"] <= 0:
            raise ValueError("El valor UF debe ser mayor a 0")
        if not (0 < parametros_temp["tasa_afp"] < 1):
            raise ValueError("La tasa AFP debe estar entre 0 y 1")
        if not (0 < parametros_temp["tasa_salud"] < 1):
            raise ValueError("La tasa de salud debe estar entre 0 y 1")

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
            hasta_texto = f"{tramo['hasta']:,.0f}".replace(',', '.') if tramo['hasta'] != float('inf') else "∞"
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
        hasta_var = tk.StringVar(value=str(tramo.get('hasta', '')) if tramo.get('hasta', 0) != float('inf') else '')
        tasa_var = tk.StringVar(value=str(tramo.get('tasa', '')))
        rebaja_var = tk.StringVar(value=str(tramo.get('rebaja', '')))
        infinito_var = tk.BooleanVar(value=tramo.get('hasta', 0) == float('inf'))

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
                hasta = float('inf') if infinito_var.get() else float(hasta_var.get().replace('.', '').replace(',', ''))
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

    #----
    #    Cálculo Mejorado - CORREGIDO
    #----
    def get_tasa_afp(self) -> float:
        """Obtiene la tasa de AFP seleccionada"""
        afp_tasas = {
            'AFP Uno (10.49%)': 0.1049,
            'Cuprum (10.44%)': 0.1044,
            'Habitat (10.77%)': 0.1077,
            'Planvital (10.16%)': 0.1016,
            'ProVida (10.55%)': 0.1055,
            'Capital (11.44%)': 0.1144,
            'Modelo (10.58%)': 0.1058
        }
        return afp_tasas.get(self.afp_var.get(), self.parametros["tasa_afp"])

    def impuesto_unico(self, base: float) -> float:
        """
        Devuelve el impuesto de 2ª categoría para una base tributable mensual.
        Usa fórmula:   impuesto = base * tasa – rebaja
        CORREGIDO: Reconoce el tramo "infinito" con float('inf')
        """
        if base <= 0:
            return 0.0

        for tramo in self.tramos_impuesto:
            if tramo["desde"] <= base <= tramo["hasta"]:
                return max(base * tramo["tasa"] - tramo["rebaja"], 0.0)

        # Por seguridad (no debería ocurrir)
        tramo_top = max(self.tramos_impuesto, key=lambda t: t["desde"])
        return max(base * tramo_top["tasa"] - tramo_top["rebaja"], 0.0)

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
            
        return None

    def mostrar_resultados_popup(self, **kwargs):
        """Muestra los resultados del cálculo en una ventana popup"""
        try:
            # Crear ventana de resultados
            resultado_win = tk.Toplevel(self.root)
            resultado_win.title("📊 Resultados del Cálculo")
            resultado_win.geometry("650x750+250+50")
            resultado_win.configure(bg='#f8f9fa')
            resultado_win.grab_set()
            resultado_win.resizable(False, False)

            # Frame principal con scroll
            main_frame = tk.Frame(resultado_win, bg='#f8f9fa')
            main_frame.pack(fill='both', expand=True, padx=20, pady=15)

            # Título principal
            title_frame = tk.Frame(main_frame, bg='#2c3e50', height=50)
            title_frame.pack(fill='x', pady=(0, 15))
            title_frame.pack_propagate(False)

            tk.Label(title_frame, text="Resultados del Cálculo de Sueldo",
                    font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50').pack(expand=True)

            # Frame de contenido
            content_frame = tk.Frame(main_frame, bg='#f8f9fa')
            content_frame.pack(fill='both', expand=True)

            # Sección 1: Resumen Principal
            self._crear_seccion_resumen(content_frame, kwargs)

            # Sección 2: Detalle de Haberes
            self._crear_seccion_haberes(content_frame, kwargs)

            # Sección 3: Detalle de Descuentos
            self._crear_seccion_descuentos(content_frame, kwargs)

            # Sección 4: Información Adicional
            self._crear_seccion_info_adicional(content_frame, kwargs)

            # Botones
            self._crear_botones_resultado(main_frame, resultado_win, kwargs)

        except Exception as e:
            messagebox.showerror("Error", f"Error mostrando resultados: {e}")

    def _crear_seccion_resumen(self, parent, datos):
        """Crea la sección de resumen principal"""
        resumen_frame = tk.LabelFrame(parent, text="📋 Resumen Principal",
                                     font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#2c3e50',
                                     padx=15, pady=10)
        resumen_frame.pack(fill='x', pady=(0, 10))

        # Datos principales
        datos_principales = [
            ("Sueldo Líquido Deseado:", f"${datos['deseado']:,.0f}"),
            ("Sueldo Base Calculado:", f"${datos['base']:,.0f}"),
            ("Sueldo Líquido Obtenido:", f"${datos['liquido']:,.0f}"),
            ("Diferencia:", f"${datos['diferencia']:,.0f}" + 
             (" ✅" if abs(datos['diferencia']) <= 1000 else " ⚠️"))
        ]

        for i, (label, valor) in enumerate(datos_principales):
            tk.Label(resumen_frame, text=label, font=('Arial', 10, 'bold'),
                    bg='#f8f9fa', anchor='w').grid(row=i, column=0, sticky='w', padx=5, pady=3)
            
            color = '#27ae60' if 'Obtenido' in label else '#2c3e50'
            if 'Diferencia' in label and abs(datos['diferencia']) > 1000:
                color = '#e74c3c'
                
            tk.Label(resumen_frame, text=valor, font=('Arial', 10),
                    bg='#f8f9fa', fg=color, anchor='e').grid(row=i, column=1, sticky='e', padx=5, pady=3)

        # Configurar columnas
        resumen_frame.grid_columnconfigure(0, weight=1)
        resumen_frame.grid_columnconfigure(1, weight=1)

    def _crear_seccion_haberes(self, parent, datos):
        """Crea la sección de detalle de haberes"""
        haberes_frame = tk.LabelFrame(parent, text="💰 Detalle de Haberes",
                                     font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#27ae60',
                                     padx=15, pady=10)
        haberes_frame.pack(fill='x', pady=(0, 10))

        haberes_items = [
            ("Sueldo Base:", f"${datos['base']:,.0f}"),
            ("Gratificación:", f"${datos['grat']:,.0f}"),
            ("Bonos Imponibles:", f"${datos['bonos_imp']:,.0f}"),
            ("Bonos No Imponibles:", f"${datos['bonos_noimp']:,.0f}"),
            ("Movilización:", f"${datos['mov']:,.0f}"),
        ]

        for i, (label, valor) in enumerate(haberes_items):
            tk.Label(haberes_frame, text=label, font=('Arial', 9),
                    bg='#f8f9fa', anchor='w').grid(row=i, column=0, sticky='w', padx=5, pady=2)
            tk.Label(haberes_frame, text=valor, font=('Arial', 9),
                    bg='#f8f9fa', anchor='e').grid(row=i, column=1, sticky='e', padx=5, pady=2)

        # Separador
        tk.Frame(haberes_frame, height=1, bg='#bdc3c7').grid(row=len(haberes_items), column=0, 
                                                             columnspan=2, sticky='ew', pady=5)

        # Total haberes
        tk.Label(haberes_frame, text="Total Haberes:", font=('Arial', 10, 'bold'),
                bg='#f8f9fa', fg='#27ae60', anchor='w').grid(row=len(haberes_items)+1, column=0, 
                                                            sticky='w', padx=5, pady=3)
        tk.Label(haberes_frame, text=f"${datos['hab']:,.0f}", font=('Arial', 10, 'bold'),
                bg='#f8f9fa', fg='#27ae60', anchor='e').grid(row=len(haberes_items)+1, column=1, 
                                                            sticky='e', padx=5, pady=3)

        haberes_frame.grid_columnconfigure(0, weight=1)
        haberes_frame.grid_columnconfigure(1, weight=1)

    def _crear_seccion_descuentos(self, parent, datos):
        """Crea la sección de detalle de descuentos"""
        desc_frame = tk.LabelFrame(parent, text="📉 Detalle de Descuentos",
                                  font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#e74c3c',
                                  padx=15, pady=10)
        desc_frame.pack(fill='x', pady=(0, 10))

        descuentos_items = [
            ("AFP:", f"${datos['afp']:,.0f}"),
            ("Salud:", f"${datos['salud']:,.0f}"),
            ("Cesantía:", f"${datos['cesant']:,.0f}"),
            ("Impuesto 2ª Categoría:", f"${datos['imp']:,.0f}"),
        ]

        for i, (label, valor) in enumerate(descuentos_items):
            tk.Label(desc_frame, text=label, font=('Arial', 9),
                    bg='#f8f9fa', anchor='w').grid(row=i, column=0, sticky='w', padx=5, pady=2)
            tk.Label(desc_frame, text=valor, font=('Arial', 9),
                    bg='#f8f9fa', anchor='e').grid(row=i, column=1, sticky='e', padx=5, pady=2)

        # Separador
        tk.Frame(desc_frame, height=1, bg='#bdc3c7').grid(row=len(descuentos_items), column=0, 
                                                          columnspan=2, sticky='ew', pady=5)

        # Total descuentos
        tk.Label(desc_frame, text="Total Descuentos:", font=('Arial', 10, 'bold'),
                bg='#f8f9fa', fg='#e74c3c', anchor='w').grid(row=len(descuentos_items)+1, column=0, 
                                                            sticky='w', padx=5, pady=3)
        tk.Label(desc_frame, text=f"${datos['desc']:,.0f}", font=('Arial', 10, 'bold'),
                bg='#f8f9fa', fg='#e74c3c', anchor='e').grid(row=len(descuentos_items)+1, column=1, 
                                                            sticky='e', padx=5, pady=3)

        desc_frame.grid_columnconfigure(0, weight=1)
        desc_frame.grid_columnconfigure(1, weight=1)

    def _crear_seccion_info_adicional(self, parent, datos):
        """Crea la sección de información adicional"""
        info_frame = tk.LabelFrame(parent, text="ℹ️ Información Adicional",
                                  font=('Arial', 11, 'bold'), bg='#f8f9fa', fg='#7f8c8d',
                                  padx=15, pady=10)
        info_frame.pack(fill='x', pady=(0, 10))

        info_items = [
            ("Sueldo Bruto Imponible:", f"${datos['imponible']:,.0f}"),
            ("Base Tributable:", f"${datos['base_trib']:,.0f}"),
            ("Tope Imponible (87.8 UF):", f"${datos['tope_imp']:,.0f}"),
            ("Iteraciones de Cálculo:", f"{datos.get('iteraciones', 'N/A')}"),
        ]

        for i, (label, valor) in enumerate(info_items):
            tk.Label(info_frame, text=label, font=('Arial', 9),
                    bg='#f8f9fa', fg='#7f8c8d', anchor='w').grid(row=i, column=0, sticky='w', padx=5, pady=2)
            tk.Label(info_frame, text=valor, font=('Arial', 9),
                    bg='#f8f9fa', fg='#7f8c8d', anchor='e').grid(row=i, column=1, sticky='e', padx=5, pady=2)

        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

    def _crear_botones_resultado(self, parent, ventana, datos):
        """Crea los botones de la ventana de resultados"""
        btn_frame = tk.Frame(parent, bg='#f8f9fa')
        btn_frame.pack(pady=15)

        # Botón Exportar
        tk.Button(btn_frame, text="📄 Exportar Resultados", 
                 command=lambda: self.exportar_resultados(datos),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=8).pack(side='left', padx=10)

        # Botón Cerrar
        tk.Button(btn_frame, text="❌ Cerrar", command=ventana.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                 relief='flat', padx=20, pady=8).pack(side='left', padx=10)

    def exportar_resultados(self, datos):
        """Exporta los resultados a un archivo de texto"""
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"calculo_sueldo_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("CALCULADORA DE SUELDOS - RESULTADOS\n")
                f.write("=" * 60 + "\n")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
                
                f.write("RESUMEN PRINCIPAL:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Sueldo Líquido Deseado:    ${datos['deseado']:>12,.0f}\n")
                f.write(f"Sueldo Base Calculado:     ${datos['base']:>12,.0f}\n")
                f.write(f"Sueldo Líquido Obtenido:   ${datos['liquido']:>12,.0f}\n")
                f.write(f"Diferencia:                ${datos['diferencia']:>12,.0f}\n\n")
                
                f.write("DETALLE DE HABERES:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Sueldo Base:               ${datos['base']:>12,.0f}\n")
                f.write(f"Gratificación:             ${datos['grat']:>12,.0f}\n")
                f.write(f"Bonos Imponibles:          ${datos['bonos_imp']:>12,.0f}\n")
                f.write(f"Bonos No Imponibles:       ${datos['bonos_noimp']:>12,.0f}\n")
                f.write(f"Movilización:              ${datos['mov']:>12,.0f}\n")
                f.write(f"TOTAL HABERES:             ${datos['hab']:>12,.0f}\n\n")
                
                f.write("DETALLE DE DESCUENTOS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"AFP:                       ${datos['afp']:>12,.0f}\n")
                f.write(f"Salud:                     ${datos['salud']:>12,.0f}\n")
                f.write(f"Cesantía:                  ${datos['cesant']:>12,.0f}\n")
                f.write(f"Impuesto 2ª Categoría:     ${datos['imp']:>12,.0f}\n")
                f.write(f"TOTAL DESCUENTOS:          ${datos['desc']:>12,.0f}\n\n")
                
                f.write("INFORMACIÓN ADICIONAL:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Sueldo Bruto Imponible:    ${datos['imponible']:>12,.0f}\n")
                f.write(f"Base Tributable:           ${datos['base_trib']:>12,.0f}\n")
                f.write(f"Tope Imponible (87.8 UF):  ${datos['tope_imp']:>12,.0f}\n")
                f.write(f"Iteraciones de Cálculo:    {datos.get('iteraciones', 'N/A'):>12}\n")
                
            messagebox.showinfo("Exportación Exitosa", 
                              f"Resultados exportados a:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error exportando resultados: {e}")


#----
#    Función Principal
#----
def main():
    """Función principal de la aplicación"""
    try:
        root = tk.Tk()
        app = CalculadoraSueldos(root)
        
        # Configurar cierre de aplicación
        def on_closing():
            if messagebox.askokcancel("Salir", "¿Desea cerrar la aplicación?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Iniciar aplicación
        print("🚀 Iniciando Calculadora de Sueldos...")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        messagebox.showerror("Error Crítico", 
                           f"Error al iniciar la aplicación:\n{e}")

if __name__ == "__main__":
    main()