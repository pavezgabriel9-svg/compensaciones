"""
    Interfaz gráfica para la gestión de alertas de contratos.
"""

#importaciones
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

#configuracion interfaz
class ConfigUI:
    
    def __init__(self):
        """Inicializa la ventana principal"""
        # Inicializar callbacks como None
        self.enviar_selecionada_callback = None
        self.enviar_seleccionadas_por_jefe_callback = None
        
        # Inicializar dataframes vacíos
        self.alertas_df = pd.DataFrame()
        self.incidencias_df = pd.DataFrame()
        
        # Crear ventana
        self.root = tk.Tk()
        self._ventana_principal()
        self.configuracion_ventana()
    
    def _ventana_principal(self):
        """Configura la ventana principal"""
        self.root.title("Alertas de Contratos")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        self.root.minsize(600, 400)
    
    def configuracion_ventana(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Secciones
        self._crear_seccion_metricas(main_frame)
        self._crear_seccion_tabla(main_frame)

    def _crear_seccion_metricas(self, parent):
        """Crea la sección de métricas principales"""
        metrics_frame = tk.LabelFrame(parent, text="Resumen de Alertas", 
                                     font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                     padx=15, pady=15)
        metrics_frame.pack(fill='x', pady=(0, 10))

        # Frame para métricas en fila
        metrics_row = tk.Frame(metrics_frame, bg='#f0f0f0')
        metrics_row.pack(fill='x')

        # Variables para métricas
        self.total_alertas_var = tk.StringVar(value="0")
        self.urgentes_var = tk.StringVar(value="0")
        self.requieren_accion_var = tk.StringVar(value="0")
        self.jefes_afectados_var = tk.StringVar(value="0")

        # Crear métricas
        self._crear_metrica(metrics_row, "Total Alertas", self.total_alertas_var, '#3498db')
        self._crear_metrica(metrics_row, "Jefes por Notificar", self.jefes_afectados_var, '#9b59b6')

    def _crear_metrica(self, parent, titulo, variable, color):
        """Crea una métrica individual"""
        metric_frame = tk.Frame(parent, bg=color, relief='raised', bd=2)
        metric_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        tk.Label(metric_frame, text=titulo, font=('Arial', 10, 'bold'), 
                fg='white', bg=color).pack(pady=(10, 5))
        
        tk.Label(metric_frame, textvariable=variable, font=('Arial', 18, 'bold'), 
                fg='white', bg=color).pack(pady=(0, 10))
        
    def _crear_seccion_tabla(self, parent):
        """Crea la sección de tabla de alertas"""
        tabla_frame = tk.LabelFrame(parent, text="Filtros y Acciones", 
                                font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                padx=10, pady=10)
        tabla_frame.pack(fill='both', expand=True, pady=(0, 10))

        # frame filtros
        filtros_frame = tk.Frame(tabla_frame, bg='#f0f0f0')
        filtros_frame.pack(fill='x', pady=(0, 10))

        # Filtro 
        self.filtro_var = tk.StringVar(value="Todos")
        filtro_combo = ttk.Combobox(filtros_frame, textvariable=self.filtro_var, 
                                values=["Todos", "SEGUNDO_PLAZO", "INDEFINIDO"],
                                state="readonly", width=15)
        filtro_combo.pack(side='left', padx=5)
        filtro_combo.bind('<<ComboboxSelected>>', self.aplicar_filtro)

        tk.Button(filtros_frame, text="Enviar Alertas Seleccionadas", 
                command=self._enviar_seleccionadas,
                bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'), 
                relief='flat', padx=17, pady=10).pack(side='left', padx=5)
        
        # botón resumen por jefe
        tk.Button(filtros_frame, text="Resumen por Jefe", 
                command=self._mostrar_resumen_jefes,
                bg='#9b59b6', fg='white', font=('Arial', 10), 
                relief='flat', padx=17, pady=10).pack(side='left', padx=5)
        
        # Crear Treeview
        self._crear_tabla(tabla_frame)
    
    def _crear_tabla(self, parent):
        """Crea el treeview para mostrar alertas"""
        tabla_frame = tk.Frame(parent, bg='#f0f0f0')
        tabla_frame.pack(fill='both', expand=True)

        # Columnas
        columns = ('Empleado', 'Cargo', 'Jefe', 'Fecha Vencimiento', 'Vencimiento', 'Motivo')
        
        self.alertas_tree = ttk.Treeview(tabla_frame, columns=columns, show='headings', 
                                        height=15, selectmode='extended')
        
        # Configurar columnas
        anchos = [200, 150, 200, 120, 50, 150]
        for i, col in enumerate(columns):
            self.alertas_tree.heading(col, text=col)
            self.alertas_tree.column(col, width=anchos[i], anchor='center')

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tabla_frame, orient='vertical', command=self.alertas_tree.yview)
        self.alertas_tree.configure(yscrollcommand=scrollbar_v.set)

        # Pack
        self.alertas_tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')

    def _enviar_seleccionadas(self):
        """Llama al callback para enviar alertas seleccionadas"""
        if self.enviar_selecionada_callback:
            self.enviar_selecionada_callback()
            
    def _enviar_seleccionadas_por_jefe(self):
        """Llama al callback para enviar alertas seleccionadas"""
        if self.enviar_seleccionadas_por_jefe_callback:
            self.enviar_seleccionadas_por_jefe_callback()

    def actualizar_metricas(self):
        """Actualiza las métricas en la interfaz"""
        if self.alertas_df.empty:
            self.total_alertas_var.set("0")
            self.jefes_afectados_var.set("0")
        else:
            self.total_alertas_var.set(str(len(self.alertas_df)))
            self.jefes_afectados_var.set(str(self.alertas_df["Jefe"].nunique()))

    def actualizar_tabla(self):
        """Actualiza la tabla de alertas"""
        for item in self.alertas_tree.get_children():
            self.alertas_tree.delete(item)

        if self.alertas_df.empty:
            return

        # Aplicar filtro actual
        df_filtrado = self.aplicar_filtro_actual()

        # Llenar tabla
        for _, row in df_filtrado.iterrows():
            try:
                valores = (
                    row["Empleado"], 
                    row["Cargo"], 
                    row["Jefe"], 
                    row["Fecha Vencimiento"],
                    row["Vencimiento"],
                    row["Motivo"]
                    
                )
                item = self.alertas_tree.insert('', 'end', values=valores)
                
            except KeyError as e:
                print(f"Error accediendo a columna: {e}")
                print(f"Columnas disponibles: {list(row.index)}")
                break
            except Exception as e:
                print(f"Error general en fila: {e}")
                continue

    def aplicar_filtro_actual(self):
        """Aplica el filtro seleccionado"""
        if self.alertas_df.empty:
            return self.alertas_df

        filtro = self.filtro_var.get()
        
        if filtro == "Todos":
            return self.alertas_df
        elif filtro in ["SEGUNDO_PLAZO", "INDEFINIDO"]:
            return self.alertas_df[self.alertas_df["Tipo Alerta"] == filtro]
        else:
            return self.alertas_df

    def aplicar_filtro(self, event=None):
        """Aplica filtro cuando cambia la selección"""
        self.actualizar_tabla()
        
    
    def _mostrar_resumen_jefes(self):
        """Muestra ventana con resumen por jefe"""
        if self.alertas_df.empty:
            messagebox.showinfo("Sin datos", "No hay alertas para mostrar resumen.")
            return

        # Crear ventana de resumen
        ventana_resumen = tk.Toplevel(self.root)
        ventana_resumen.title("Resumen por Jefe")
        ventana_resumen.geometry("800x600+200+100")
        ventana_resumen.configure(bg='#f0f0f0')
        ventana_resumen.grab_set()

        # Título
        tk.Label(ventana_resumen, text="Alertas por Jefe", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Crear treeview para resumen
        columns = ('Jefe', 'Email', 'Empleados Afectados')
        resumen_tree = ttk.Treeview(ventana_resumen, columns=columns, show='headings', height=15)
        
        for col in columns:
            resumen_tree.heading(col, text=col)
            resumen_tree.column(col, width=150, anchor='w')

        # Calcular resumen por jefe
        resumen_jefes = self.alertas_df.groupby(['Jefe', 'Email Jefe']).agg({
            'Empleado': 'nunique'
        }).reset_index()

        # Llenar treeview
        for _, row in resumen_jefes.iterrows():
            resumen_tree.insert('', 'end', values=(
                row['Jefe'], row['Email Jefe'], row['Empleado']
            ))

        resumen_tree.pack(fill='both', expand=True, padx=20, pady=10)

        def _obtener_y_enviar_jefes_seleccionados():
            """
            Obtiene los jefes seleccionados del resumen_tree local,
            y llama al callback de servicio con el filtro (jefes_filtro).
            """
            seleccionados_ids = resumen_tree.selection()
            
            if not seleccionados_ids:
                messagebox.showwarning("Sin selección", "Por favor selecciona al menos un jefe para notificar.")
                return
            
            jefes_a_filtrar = []
            for item_id in seleccionados_ids:
                # Los valores del Treeview son (Jefe, Email Jefe, Empleados Afectados)
                valores = resumen_tree.item(item_id)['values']
                jefe = valores[0]
                email = valores[1]
                # Creamos el diccionario para el filtro que espera services.py
                jefes_a_filtrar.append({'Jefe': jefe, 'Email Jefe': email})
                
            # AQUI SE LLAMA AL CALLBACK Y SE PASA EL ARGUMENTO REQUERIDO
            if self.enviar_seleccionadas_por_jefe_callback:
                self.enviar_seleccionadas_por_jefe_callback(jefes_a_filtrar)
                
            # Cerrar la ventana después de la acción (opcional, pero buena práctica)
            ventana_resumen.destroy()


        # Botón cerrar
        tk.Button(ventana_resumen, text="Cerrar", command=ventana_resumen.destroy,
                 bg='#FF6961', fg='white', font=('Arial', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(side='left', pady=15, padx=5)

        # boton envio masivo (LLAMA A LA FUNCIÓN INTERNA QUE PASA EL ARGUMENTO)
        tk.Button(ventana_resumen, text="Enviar Alertas por Jefe", command=_obtener_y_enviar_jefes_seleccionados,
                 bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(side='left', pady=15, padx=5)

    
    
    def run(self):
        self.root.mainloop()    
