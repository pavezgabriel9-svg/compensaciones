import tkinter as tk
from tkinter import ttk, messagebox
import math

class CalculadoraSueldos:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Sueldos Chile 2025")
        self.root.geometry("800x700")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.sueldo_liquido_var = tk.StringVar()
        self.precision_var = tk.StringVar(value="100")
        self.afp_var = tk.StringVar(value="AFP Uno (10.49%)")
        self.salud_var = tk.StringVar(value="Fonasa (7%)")
        self.movilizacion_var = tk.StringVar(value="40000")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Título principal
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill='x', padx=0, pady=0)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="💰 Calculadora de Sueldos Chile 2025", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Sección de entrada
        input_frame = tk.LabelFrame(main_frame, text="Datos de Entrada", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        input_frame.pack(fill='x', pady=(0, 20))
        
        # Sueldo líquido deseado
        tk.Label(input_frame, text="Sueldo Líquido Deseado ($):", 
                font=('Arial', 10), bg='#f0f0f0').grid(row=0, column=0, sticky='w', padx=10, pady=10)
        
        sueldo_entry = tk.Entry(input_frame, textvariable=self.sueldo_liquido_var, 
                               font=('Arial', 12), width=15)
        sueldo_entry.grid(row=0, column=1, padx=10, pady=10)
        sueldo_entry.bind('<KeyRelease>', self.format_currency)
        
        # AFP
        tk.Label(input_frame, text="AFP:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=1, column=0, sticky='w', padx=10, pady=5)
        
        afp_combo = ttk.Combobox(input_frame, textvariable=self.afp_var, width=20, state='readonly')
        afp_combo['values'] = ('AFP Uno (10.49%)', 'Cuprum (10.44%)', 'Habitat (10.77%)', 
                              'Planvital (10.16%)', 'ProVida (10.55%)', 'Capital (11.44%)', 'Modelo (10.58%)')
        afp_combo.grid(row=1, column=1, padx=10, pady=5)
        
        # Sistema de Salud
        tk.Label(input_frame, text="Sistema de Salud:", font=('Arial', 10), bg='#f0f0f0').grid(
            row=2, column=0, sticky='w', padx=10, pady=5)
        
        salud_combo = ttk.Combobox(input_frame, textvariable=self.salud_var, width=20, state='readonly')
        salud_combo['values'] = ('Fonasa (7%)', 'Isapre (7% + plan)')
        salud_combo.grid(row=2, column=1, padx=10, pady=5)
        
        # Movilización
        tk.Label(input_frame, text="Movilización ($):", font=('Arial', 10), bg='#f0f0f0').grid(
            row=3, column=0, sticky='w', padx=10, pady=5)
        
        mov_entry = tk.Entry(input_frame, textvariable=self.movilizacion_var, 
                            font=('Arial', 10), width=15)
        mov_entry.grid(row=3, column=1, padx=10, pady=5)
        
        # Botón calcular
        calc_button = tk.Button(input_frame, text="🧮 Calcular Sueldo Base", 
                               command=self.calcular, font=('Arial', 12, 'bold'),
                               bg='#3498db', fg='white', relief='flat', padx=20, pady=10)
        calc_button.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Frame de resultados
        self.result_frame = tk.LabelFrame(main_frame, text="Resultados del Cálculo", 
                                         font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50')
        self.result_frame.pack(fill='both', expand=True)
        
        # Text widget para mostrar resultados
        self.result_text = tk.Text(self.result_frame, font=('Courier', 10), 
                                  bg='white', fg='#2c3e50', wrap='word', height=20)
        
        scrollbar = tk.Scrollbar(self.result_frame, orient='vertical', command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        self.result_text.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
    def format_currency(self, event):
        """Formatea el input como moneda chilena"""
        value = self.sueldo_liquido_var.get().replace('.', '').replace(',', '')
        if value.isdigit():
            formatted = f"{int(value):,}".replace(',', '.')
            self.sueldo_liquido_var.set(formatted)
            
    def get_tasa_afp(self):
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
        return afp_tasas.get(self.afp_var.get(), 0.1049)
    
    def impuesto_unico(self, imponible):
        """Calcula impuesto único según tramos SII 2025"""
        tramos = [
            (0, 926_734.50, 0.0, 0.0),
            (926_734.51, 2_059_410.00, 0.04, 37_069.38),
            (2_059_410.01, 3_432_350.00, 0.08, 119_445.78),
            (3_432_350.01, 4_805_290.00, 0.135, 308_225.03),
            (4_805_290.01, 6_178_230.00, 0.23, 764_727.58),
            (6_178_230.01, 8_237_640.00, 0.304, 1_221_916.60),
            (8_237_640.01, 21_280_570.00, 0.35, 1_600_848.04),
            (21_280_570.01, float('inf'), 0.40, 2_664_876.54),
        ]
        
        for lower, upper, factor, rebate in tramos:
            if lower <= imponible <= upper:
                impuesto = imponible * factor - rebate
                return max(impuesto, 0.0)
        return 0.0
    
    def calcular(self):
        try:
            # Validar entrada
            sueldo_str = self.sueldo_liquido_var.get().replace('.', '').replace(',', '')
            if not sueldo_str or not sueldo_str.isdigit():
                messagebox.showerror("Error", "Por favor ingrese un sueldo líquido válido")
                return
                
            sueldo_liquido_deseado = int(sueldo_str)
            movilizacion = int(self.movilizacion_var.get().replace('.', '').replace(',', ''))
            
            if sueldo_liquido_deseado <= 0:
                messagebox.showerror("Error", "El sueldo debe ser mayor a 0")
                return
            
            # Parámetros
            ingreso_minimo = 529_000
            tasa_afp = self.get_tasa_afp()
            tasa_salud = 0.07
            tasa_cesant = 0.006
            precision = 100
            
            # Búsqueda binaria
            sueldo_min = 0
            sueldo_max = sueldo_liquido_deseado * 3
            
            while sueldo_max - sueldo_min > precision:
                sueldo_base = (sueldo_min + sueldo_max) / 2
                
                # Gratificación legal
                tope_grat_mensual = 4.75 * ingreso_minimo / 12
                gratificacion = min(0.25 * sueldo_base, tope_grat_mensual)
                
                # Total imponible
                imponible = sueldo_base + gratificacion
                
                # Descuentos
                cotiz_prev = imponible * tasa_afp
                cotiz_salud = imponible * tasa_salud
                cesantia = imponible * tasa_cesant
                
                # Base tributable
                base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
                
                # Impuesto
                impuesto2cat = self.impuesto_unico(base_tributable)
                
                # Totales
                total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
                total_haberes = imponible + movilizacion
                sueldo_liquido_calculado = total_haberes - total_descuentos
                
                if sueldo_liquido_calculado < sueldo_liquido_deseado:
                    sueldo_min = sueldo_base
                else:
                    sueldo_max = sueldo_base
            
            # Resultado final
            sueldo_base = round(sueldo_base)
            
            # Recalcular con valores finales
            tope_grat_mensual = 4.75 * ingreso_minimo / 12
            gratificacion = min(0.25 * sueldo_base, tope_grat_mensual)
            imponible = sueldo_base + gratificacion
            cotiz_prev = imponible * tasa_afp
            cotiz_salud = imponible * tasa_salud
            cesantia = imponible * tasa_cesant
            base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
            impuesto2cat = self.impuesto_unico(base_tributable)
            total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
            total_haberes = imponible + movilizacion
            sueldo_liquido = total_haberes - total_descuentos
            
            # Mostrar resultados
            self.mostrar_resultados(sueldo_liquido_deseado, sueldo_base, gratificacion, 
                                  imponible, movilizacion, cotiz_prev, cotiz_salud, 
                                  cesantia, impuesto2cat, base_tributable, 
                                  total_descuentos, total_haberes, sueldo_liquido)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {str(e)}")
    
    def mostrar_resultados(self, deseado, base, grat, imponible, mov, afp, salud, 
                          cesant, imp, base_trib, desc, hab, liquido):
        """Muestra los resultados formateados"""
        resultado = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CÁLCULO DE SUELDO BASE                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 OBJETIVO
   Sueldo líquido deseado: ${deseado:,.0f}

💰 RESULTADO PRINCIPAL
   Sueldo base necesario: ${base:,.0f}

📊 DETALLE DE HABERES
   ├─ Sueldo base:              ${base:>15,.0f}
   ├─ Gratificación legal:      ${grat:>15,.0f}
   ├─ Total Imponible:          ${imponible:>15,.0f}
   └─ Haberes no imponibles:    ${mov:>15,.0f}
   
   TOTAL HABERES:               ${hab:>15,.0f}

📉 DETALLE DE DESCUENTOS
   ├─ AFP ({self.get_tasa_afp()*100:.2f}%):              ${afp:>15,.0f}
   ├─ Salud (7.00%):            ${salud:>15,.0f}
   ├─ Cesantía (0.60%):         ${cesant:>15,.0f}
   └─ Impuesto 2ª Cat.:         ${imp:>15,.0f}
   
   TOTAL DESCUENTOS:            ${desc:>15,.0f}

💵 RESULTADO FINAL
   Sueldo líquido calculado:    ${liquido:>15,.0f}
   Diferencia con deseado:      ${liquido - deseado:>15,.0f}

📋 INFORMACIÓN ADICIONAL
   ├─ Base tributable:          ${base_trib:>15,.0f}
   ├─ Tope gratificación:       ${4.75 * 529_000 / 12:>15,.0f}
   └─ Ingreso mínimo 2025:      ${529_000:>15,.0f}

═══════════════════════════════════════════════════════════════════════════════
Cálculo realizado con parámetros legales vigentes para Chile 2025
═══════════════════════════════════════════════════════════════════════════════
"""
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, resultado)

# Crear y ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = CalculadoraSueldos(root)
    root.mainloop()
