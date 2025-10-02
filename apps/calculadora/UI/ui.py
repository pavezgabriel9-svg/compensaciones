"""
    Interfaz gráfica calculadora de sueldos
"""

#importaciones
import tkinter as tk

#configuración interfaz
class ConfigUI:
    
    def __init__(self):
        """Inicializa la ventana principal"""
        
        # Creamos un placeholder para la función que vendrá del exterior
        self.format_sueldo_callback = None 

        self.root = tk.Tk()
        
        self.sueldo_liquido_var = tk.StringVar()
        
        self._configuracion_ventana()
        self._ventana_principal()

        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def _configuracion_ventana(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Secciones
        self.crear_seccion_entradas(main_frame)
        self.crear_seccion_bonos(main_frame)
        self._crear_boton_calcular(main_frame)
        #self._crear_info_parametros(main_frame)

    def _ventana_principal(self):
        """Configura la ventana principal"""
        self.root.title("Calculadora de Sueldos")
        self.root.geometry("200x500")
        self.root.configure(bg="#f0f0f0")
        self.root.minsize(600, 400)

    def crear_seccion_entradas(self, parent):
        """Crea la sección de entradas principales"""
        input_frame = tk.LabelFrame(parent, 
                                   font=('Arial', 11, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))
        self._crear_campo_sueldo(input_frame)
        self._crear_campo_afp(input_frame)
        self._crear_campo_salud(input_frame)
        self._crear_campo_movilizacion(input_frame)
        self._crear_boton_parametros(input_frame)

    def _crear_campo_sueldo(self, parent):
        """INPUT Sueldo Líquido Deseado"""
        tk.Label(parent, fg='#000000' ,text="Sueldo Líquido Deseado:", 
                font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        sueldo_entry = tk.Entry(parent, textvariable=self.sueldo_liquido_var, 
                                font=('Arial', 12), width=13)
        sueldo_entry.grid(row=0, column=1, padx=5, pady=5)
        sueldo_entry.bind('<KeyRelease>', self._manejo_formato_sueldo)

    def _manejo_formato_sueldo(self, event):
        if self.formato_chile_sueldo_callback:
            current_value = self.sueldo_liquido_var.get()
            formatted_value = self.formato_chile_sueldo_callback(current_value)     
            self.sueldo_liquido_var.set(formatted_value)


    def _crear_campo_afp(self, parent):
        """Crea el campo de AFP estático"""
        tk.Label(parent, text="AFP:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=1, column=0, sticky='e', padx=5, pady=5)
        
        # Label estático que muestra la tasa de AFP configurada
        self.afp_label = tk.Label(parent, #text=f"{self.parametros['tasa_afp']*100:.2f}%", 
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
        # self.fonasa_check = tk.Radiobutton(salud_frame, #text=f"Fonasa ({self.parametros['tasa_salud']*100:.1f}%)", 
        #                                   variable=self.tipo_salud_var, 
        #                                   value="fonasa",
        #                                   bg='#f0f0f0', font=('Arial', 9),
        #                                   command=self._actualizar_interfaz_salud)
        # self.fonasa_check.pack(anchor='w')
        
        # Checkbox Isapre con campo UF
        isapre_frame = tk.Frame(salud_frame, bg='#f0f0f0')
        isapre_frame.pack(anchor='w', fill='x')
        
        # self.isapre_check = tk.Radiobutton(isapre_frame, text="Isapre", 
        #                                   #variable=self.tipo_salud_var, 
        #                                   value="isapre",
        #                                   bg='#f0f0f0', font=('Arial', 9),
        #                                   command=self._actualizar_interfaz_salud)
        # self.isapre_check.pack(side='left')
        
        # Campo para valor UF de Isapre
        tk.Label(isapre_frame, text="UF:", bg='#f0f0f0', font=('Arial', 9)).pack(side='left', padx=(5, 2))
        # self.isapre_uf_entry = tk.Entry(isapre_frame, #textvariable=self.valor_isapre_uf_var, 
        #                                width=6, font=('Arial', 9), state='disabled')
        # self.isapre_uf_entry.pack(side='left', padx=(0, 5))
        
        # # Label para mostrar valor en pesos
        # self.isapre_pesos_label = tk.Label(isapre_frame, text="", bg='#f0f0f0', 
        #                                   font=('Arial', 8), fg='#7f8c8d')
        # self.isapre_pesos_label.pack(side='left')
        
        # # Inicializar estado
        # self._actualizar_interfaz_salud()
        
        # Bind para actualizar valor en pesos cuando cambie UF
        #self.valor_isapre_uf_var.trace('w', lambda *args: self._actualizar_valor_isapre_pesos())

    def _crear_campo_movilizacion(self, parent):
        """Crea el campo de movilización"""
        tk.Label(parent, text="Movilización ($):", font=('Arial', 10), bg='#f0f0f0').grid(
            row=3, column=0, sticky='e', padx=5, pady=5)
        mov_entry = tk.Entry(parent, #textvariable=self.movilizacion_var, 
                            font=('Arial', 10), width=13)
        mov_entry.grid(row=3, column=1, padx=5, pady=5)
        mov_entry.bind('<KeyRelease>', #self._format_currency_movilizacion
                       )

    def _crear_boton_parametros(self, parent):
        """Crea el botón de parámetros avanzados"""
        param_btn = tk.Button(parent, text="Parámetros avanzados", 
                             #command=self.abrir_parametros, 
                             font=('Arial', 10, 'bold'),
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
        tk.Entry(parent, 
                 #textvariable=self.bono_nombre_var, 
                 width=13, font=('Arial', 9)).grid(
            row=0, column=1, padx=2, pady=5)

        tk.Label(parent, text="Monto ($):", bg='#f0f0f0', font=('Arial', 9)).grid(
            row=0, column=2, padx=2, pady=5, sticky='e')
        bono_entry = tk.Entry(parent, #textvariable=self.bono_monto_var, 
                              width=10, font=('Arial', 9))
        bono_entry.grid(row=0, column=3, padx=2, pady=5)
        bono_entry.bind('<KeyRelease>', #self._format_currency_bono
                        )

        tk.Checkbutton(parent, text="Imponible", #variable=self.bono_imponible_var, 
                      bg='#f0f0f0', font=('Arial', 9)).grid(row=0, column=4, padx=2, pady=5)

        tk.Button(parent, text="➕", #command=self.agregar_bono, 
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'), relief='flat', width=3).grid(
                 row=0, column=5, padx=2, pady=5)

    def _crear_lista_bonos(self, parent):
        """Crea la lista de bonos"""
        self.bonos_listbox = tk.Listbox(parent, width=55, height=3, font=('Arial', 9))
        self.bonos_listbox.grid(row=1, column=0, columnspan=6, padx=2, pady=5, sticky='ew')
        
        tk.Button(parent, text="Eliminar Bono", #command=self.eliminar_bono, 
                 bg='#c0392b', fg='white', font=('Arial', 9, 'bold'), relief='flat').grid(
                 row=2, column=0, columnspan=6, pady=5)

    def get_info_parametros(self) -> str:
        """Muestra información actual de parámetros"""
        #tope_imponible_pesos = self.parametros["tope_imponible_uf"] * self.parametros["valor_uf"]
        #tope_grat = self.parametros["factor_gratificacion"] * self.parametros["ingreso_minimo"] / 12
        
        ancho = 100
        titulo = "Valores Utilizados".center(ancho)

        return (f"{titulo} \n"
                f"\n"
                f"Valor UF: ${self.parametros['valor_uf']:,.0f} | "
                f"Ingreso mínimo: ${self.parametros['ingreso_minimo']:,.0f} | "
                #f"Tope imponible: {self.parametros['tope_imponible_uf']} UF (${tope_imponible_pesos:,.2f}) | "
                #f"Tope gratificación: ${tope_grat:,.0f} "
                #f"Tramos impuesto: {len(self.tramos_impuesto)}").replace(',', '.'
                )



    def _crear_boton_calcular(self, parent):
        """Crea el botón de calcular"""
        calc_button = tk.Button(parent, text="Calcular Sueldo Base", 
                               #command=self.calcular, 
                               font=('Arial', 13, 'bold'),
                               bg='#008000', fg='#f0f0f0', relief='flat', padx=10, pady=10)
        calc_button.pack(pady=10, fill='x')
    
    def run(self):
        self.root.mainloop()    
