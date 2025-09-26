#-----------------------------------------------------------
#                           Importaciones
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

#entorno mac
import cryptography

#envio de correos por outlook, entorno windows
# import win32com.client as win32
# import pythoncom

#-----------------------------------------------------------
#                    Conexión BD
#-----------------------------------------------------------
# Entorno macOS
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "conexion_buk"

# Entorno Windows
# DB_HOST = "192.168.245.33"
# DB_USER = "compensaciones_rrhh"
# DB_PASSWORD = "_Cramercomp2025_"
# DB_NAME = "rrhh_app"

mail_test_gabriel = "gpavez@cramer.cl"  

#-----------------------------------------------------------
#             Dashboard de Alertas de Contratos
#-----------------------------------------------------------

class DashboardAlertas:
    """Dashboard para gestión de alertas de contratos"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._configurar_ventana_principal()
        self.alertas_df = None
        self.setup_ui()
        self.cargar_alertas()

    def _configurar_ventana_principal(self):
        """Configura la ventana principal"""
        self.root.title("Dashboard de Alertas de Contratos")
        self.root.minsize(1200, 700)
        self.root.geometry("1300x800+50+50")
        self.root.configure(bg='#f0f0f0')

    def conectar_bd(self):
        """Conecta a la base de datos"""
        try:
            return pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4"
            )
        except Exception as e:
            messagebox.showerror("Error BD", f"Error conectando a la base de datos:\n{e}")
            return None

    def obtener_alertas(self):
        """Obtiene los datos desde la base de datos"""
        conexion = self.conectar_bd()
        if not conexion:
            return pd.DataFrame()
        
        try:
            cursor = conexion.cursor()
            sql = """
            SELECT 
                id, employee_name, employee_rut, employee_role,
                employee_area_name, boss_name, boss_email,
                alert_date, alert_reason,
                days_since_start, employee_start_date,
                CAST(DATEDIFF(alert_date, CURDATE()) AS SIGNED) as dias_hasta_alerta,
                is_urgent, requires_action, alert_type
            FROM contract_alerts 
            WHERE processed = FALSE
            ORDER BY alert_date ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            cols = ["ID", "Empleado", "RUT", "Cargo", "Área", "Jefe", "Email Jefe",
                    "Fecha alerta", "Motivo", "Días desde inicio", "Fecha inicio",
                    "Días hasta alerta", "Urgente", "Requiere Acción", "Tipo Alerta"]
            
            df = pd.DataFrame(rows, columns=cols)
            cursor.close()
            conexion.close()
            return df
            
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo alertas:\n{e}")
            conexion.close()
            return pd.DataFrame()
    
    
    def obtener_incidencias(self):
        """Obtiene los datos de incidencias desde la base de datos."""
        conexion = self.conectar_bd()
        if not conexion:
            print("sin conexion")
            return pd.DataFrame()
        else:
            print("Conexión exitosa")

        try:
            cursor = conexion.cursor()
            sql = """
            SELECT
                rut_empleado AS employee_rut ,
                fecha_inicio,
                fecha_fin,
                tipo_permiso
            FROM consolidado_incidencias
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            cols = ["rut_empleado", "fecha_inicio", "fecha_fin", "tipo_permiso"]
            incidencias_df = pd.DataFrame(rows, columns=cols)
            cursor.close()
            conexion.close()
            return incidencias_df
            
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo incidencias:\n{e}")
            conexion.close()
            return pd.DataFrame()
        


    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self._crear_titulo()
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Secciones
        self.crear_seccion_metricas(main_frame)
        self.crear_seccion_tabla(main_frame)
        self.crear_seccion_acciones(main_frame)

    def _crear_titulo(self):
        """Crea el título de la aplicación"""
        title_frame = tk.Frame(self.root, bg='#e74c3c', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Alertas de Contratos", 
                              font=('Arial', 16, 'bold'), fg='white', bg='#e74c3c')
        title_label.pack(expand=True, pady=15)

    def crear_seccion_metricas(self, parent):
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

    def crear_seccion_tabla(self, parent):
        """Crea la sección de tabla de alertas"""
        tabla_frame = tk.LabelFrame(parent, text="Alertas", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        tabla_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Frame para filtros
        filtros_frame = tk.Frame(tabla_frame, bg='#f0f0f0')
        filtros_frame.pack(fill='x', pady=(0, 10))

        tk.Label(filtros_frame, text="Filtrar por:", font=('Arial', 10), bg='#f0f0f0').pack(side='left', padx=5)
        
        self.filtro_var = tk.StringVar(value="Todos")
        filtro_combo = ttk.Combobox(filtros_frame, textvariable=self.filtro_var, 
                                   values=["Todos", "SEGUNDO_PLAZO", "INDEFINIDO"],
                                   state="readonly", width=15)
        filtro_combo.pack(side='left', padx=5)
        filtro_combo.bind('<<ComboboxSelected>>', self.aplicar_filtro)

        tk.Button(filtros_frame, text="Actualizar", command=self.cargar_alertas,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'), 
                 relief='flat', padx=10, pady=5).pack(side='right', padx=5)

        # Crear Treeview
        self._crear_treeview_alertas(tabla_frame)

    def _crear_treeview_alertas(self, parent):
        """Crea el treeview para mostrar alertas con selección múltiple habilitada"""
        # Frame para treeview y scrollbar
        tree_frame = tk.Frame(parent, bg='#f0f0f0')
        tree_frame.pack(fill='both', expand=True)

        # Columnas
        columns = ('Empleado', 'Cargo', 'Jefe', 'Fecha inicio', 'Motivo')
        
        self.alertas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                        height=15, selectmode='extended')
        
        # Configurar columnas
        anchos = [200, 150, 200, 120, 150]
        for i, col in enumerate(columns):
            self.alertas_tree.heading(col, text=col)
            self.alertas_tree.column(col, width=anchos[i], anchor='w')

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=self.alertas_tree.yview)
        self.alertas_tree.configure(yscrollcommand=scrollbar_v.set)

        # Pack
        self.alertas_tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')
        
        # NUEVO: Agregar instrucciones para el usuario
        info_frame = tk.Frame(parent, bg='#f0f0f0')
        info_frame.pack(fill='x', pady=(5, 0))
        
        info_label = tk.Label(info_frame, 
                            text="Mantenga Ctrl presionado para seleccionar múltiples personas, o Shift para seleccionar un rango de personas",
                            font=('Arial', 9, 'italic'), bg='#f0f0f0', fg='#7f8c8d')
        info_label.pack(anchor='w')

    
    def crear_seccion_acciones(self, parent):
        """Crea la sección de acciones"""
        acciones_frame = tk.LabelFrame(parent, text="🚀 Acciones", 
                                    font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                    padx=15, pady=15)
        acciones_frame.pack(fill='x')

        # Frame para botones - Primera fila
        btn_frame1 = tk.Frame(acciones_frame, bg='#f0f0f0')
        btn_frame1.pack(pady=(0, 5))

        tk.Button(btn_frame1, text="Enviar Alertas Seleccionadas", 
                command=self.enviar_a_jefes_seleccionadas,
                bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'), 
                relief='flat', padx=20, pady=10).pack(side='left', padx=5)

        tk.Button(btn_frame1, text="Enviar Todas las Alertas", 
                command=self.enviar_a_todos_los_jefes,
                bg='#c0392b', fg='white', font=('Arial', 11, 'bold'), 
                relief='flat', padx=20, pady=10).pack(side='left', padx=5)

        # Frame para botones - Segunda fila (reportes de prueba)
        btn_frame2 = tk.Frame(acciones_frame, bg='#f0f0f0')
        btn_frame2.pack(pady=(5, 0))

        tk.Button(btn_frame2, text="Reporte Test (Seleccionadas)", 
                command=self.enviar_alertas_seleccionadas,
                bg='#95a5a6', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(btn_frame2, text="Resumen por Jefe", 
                command=self.mostrar_resumen_jefes,
                bg='#9b59b6', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8).pack(side='left', padx=5)

        tk.Button(btn_frame2, text="Marcar como Procesada", 
                command=self.marcar_procesada,
                bg='#27ae60', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8).pack(side='left', padx=5)
    
    def enviar_a_jefes_seleccionadas(self):
        """Envía alertas seleccionadas a los jefes correspondientes"""
        alertas_seleccionadas = self.obtener_alertas_seleccionadas()
        
        if alertas_seleccionadas.empty:
            messagebox.showwarning("Sin selección", "Debe seleccionar al menos una alerta para enviar.\n\nTip: Mantenga Ctrl presionado para seleccionar múltiples filas.")
            return
        
        # Agrupar por jefe
        alertas_por_jefe = alertas_seleccionadas.groupby(['Jefe', 'Email Jefe'])
        num_jefes = len(alertas_por_jefe)
        num_alertas = len(alertas_seleccionadas)
        
        # Mostrar ventana de confirmación
        if self.mostrar_confirmacion_envio(alertas_por_jefe, num_jefes, num_alertas, "seleccionadas"):
            self.procesar_envio_a_jefes(alertas_por_jefe, "seleccionadas")
    
    def enviar_a_todos_los_jefes(self):
        """Envía todas las alertas a los jefes correspondientes"""
        if self.alertas_df.empty:
            messagebox.showwarning("Sin datos", "No hay alertas activas para enviar.")
            return
        
        # Agrupar todas las alertas por jefe
        alertas_por_jefe = self.alertas_df.groupby(['Jefe', 'Email Jefe'])
        num_jefes = len(alertas_por_jefe)
        num_alertas = len(self.alertas_df)
        
        # Mostrar ventana de confirmación
        if self.mostrar_confirmacion_envio(alertas_por_jefe, num_jefes, num_alertas, "todas"):
            self.procesar_envio_a_jefes(alertas_por_jefe, "todas")
    
    def mostrar_confirmacion_envio(self, alertas_por_jefe, num_jefes, num_alertas, tipo_envio):
        """Muestra ventana de confirmación antes del envío"""
        resultado = self._mostrar_ventana_confirmacion(alertas_por_jefe, num_jefes, num_alertas, tipo_envio)
        self.resultado_confirmacion = resultado  # Guardar para usar en procesar_envio_a_jefes
        return resultado.get('enviar', False)
    
    def _mostrar_ventana_confirmacion(self, alertas_por_jefe, num_jefes, num_alertas, tipo_envio):
        """Muestra ventana de confirmación antes del envío"""
        # Crear ventana de confirmación
        confirm_win = tk.Toplevel(self.root)
        confirm_win.title("Confirmar Envío de Alertas")
        confirm_win.geometry("600x500+300+200")
        confirm_win.configure(bg='#f0f0f0')
        confirm_win.grab_set()
        confirm_win.resizable(False, False)
        
        # Variable para el resultado
        resultado = {'enviar': False}
            
        # Variable para el resultado
        resultado = {'enviar': False}
        
        # Título
        tk.Label(confirm_win, text="📧 Confirmación de Envío", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)
        
        # Resumen
        resumen_text = f"Se enviarán {num_alertas} alerta(s) {tipo_envio} a {num_jefes} jefe(s):"
        tk.Label(confirm_win, text=resumen_text, 
                font=('Arial', 12), bg='#f0f0f0', fg='#2c3e50').pack(pady=10)
        
        # Frame para la lista de jefes
        lista_frame = tk.LabelFrame(confirm_win, text="Detalle de envíos", 
                                font=('Arial', 10, 'bold'), bg='#f0f0f0')
        lista_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Crear Treeview para mostrar el detalle
        columns = ('Jefe', 'Email', 'Alertas')
        tree = ttk.Treeview(lista_frame, columns=columns, show='headings', height=12)
        
        # Configurar columnas
        tree.heading('Jefe', text='Jefe')
        tree.heading('Email', text='Email')
        tree.heading('Alertas', text='# Alertas')
        tree.column('Jefe', width=180)
        tree.column('Email', width=200)
        tree.column('Alertas', width=80, anchor='center')
        
        # Llenar con datos
        for (jefe, email), group in alertas_por_jefe:
            empleados = ", ".join(group['Empleado'].tolist()[:2])
            if len(group) > 2:
                empleados += f" (+{len(group)-2} más)"
            tree.insert('', 'end', values=(jefe, email, len(group)))
        
        # Scrollbar para el tree
        scrollbar = ttk.Scrollbar(lista_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Frame para opciones adicionales
        opciones_frame = tk.LabelFrame(confirm_win, text="Opciones de envío", 
                                    font=('Arial', 10, 'bold'), bg='#f0f0f0')
        opciones_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Checkbox para enviar copia a RRHH
        enviar_copia_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opciones_frame, text=f"Enviar copia (CC) a RRHH ({mail_test_gabriel})", 
                    variable=enviar_copia_var, bg='#f0f0f0', 
                    font=('Arial', 9)).pack(anchor='w', padx=10, pady=5)
        
        # Checkbox para modo de prueba
        modo_prueba_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opciones_frame, text=f"Modo prueba (enviar todo a {mail_test_gabriel} en lugar de a los jefes)", 
                    variable=modo_prueba_var, bg='#f0f0f0', fg='#e67e22',
                    font=('Arial', 9)).pack(anchor='w', padx=10, pady=5)
        
        # Frame para botones
        btn_frame = tk.Frame(confirm_win, bg='#f0f0f0')
        btn_frame.pack(pady=15)
        
        def confirmar():
            resultado['enviar'] = True
            resultado['enviar_copia'] = enviar_copia_var.get()
            resultado['modo_prueba'] = modo_prueba_var.get()
            confirm_win.destroy()
        
        def cancelar():
            resultado['enviar'] = False
            confirm_win.destroy()
    
        tk.Button(btn_frame, text="✅ Enviar", command=confirmar,
                bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                relief='flat', padx=30, pady=10).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="❌ Cancelar", command=cancelar,
                bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                relief='flat', padx=30, pady=10).pack(side='left', padx=10)
            
        # Esperar a que se cierre la ventana
        confirm_win.wait_window()
        
        return resultado
        
    
    def obtener_alertas_seleccionadas(self):
        """Obtiene las alertas seleccionadas del TreeView"""
        seleccionadas = self.alertas_tree.selection()
        if not seleccionadas:
            return pd.DataFrame()
        
        # Obtener índices de las filas seleccionadas
        indices_seleccionados = []
        df_filtrado = self.aplicar_filtro_actual()
        
        for item in seleccionadas:
            # Obtener los valores de la fila seleccionada
            valores = self.alertas_tree.item(item, 'values')
            if valores:
                empleado_nombre = valores[0]  # Primer valor es el nombre del empleado
                # Buscar el índice en el DataFrame filtrado
                mask = df_filtrado['Empleado'] == empleado_nombre
                if mask.any():
                    indices_seleccionados.extend(df_filtrado[mask].index.tolist())
        
        # Retornar las filas seleccionadas del DataFrame original
        if indices_seleccionados:
            return self.alertas_df.loc[indices_seleccionados]
        else:
            return pd.DataFrame()

    def procesar_envio_a_jefes(self, alertas_por_jefe, tipo_envio):
        """Procesa el envío de correos a los jefes"""
        resultado = self.resultado_confirmacion
        
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch("outlook.application")
            
            enviados_exitosos = 0
            errores = []
            
            # Crear barra de progreso
            progress_win = self.crear_ventana_progreso(len(alertas_por_jefe))
            
            for i, ((jefe, email_jefe), alertas_jefe) in enumerate(alertas_por_jefe):
                try:
                    self.actualizar_progreso(progress_win, i+1, len(alertas_por_jefe), f"Enviando a {jefe}...")
                    
                    mail = outlook.CreateItem(0)
                    
                    # Configurar destinatarios según el modo
                    if resultado.get('modo_prueba', False):
                        mail.To = mail_test_gabriel
                        mail.Subject = f"[PRUEBA] Alertas para {jefe} - {datetime.now().strftime('%d/%m/%Y')}"
                    else:
                        mail.To = email_jefe
                        mail.Subject = f"Alertas de contratos de su equipo - {datetime.now().strftime('%d/%m/%Y')}"
                        
                        # Agregar CC a RRHH si está habilitado
                        if resultado.get('enviar_copia', False):
                            mail.CC = mail_test_gabriel
                    
                    # Generar HTML personalizado para este jefe
                    html = self._generar_html_para_jefe(jefe, email_jefe, alertas_jefe, resultado.get('modo_prueba', False))
                    mail.HTMLBody = html
                    
                    mail.Send()
                    enviados_exitosos += 1
                    
                except Exception as e:
                    error_msg = f"Error enviando a {jefe} ({email_jefe}): {str(e)}"
                    errores.append(error_msg)
                    print(error_msg)
                    
            progress_win.destroy()
            pythoncom.CoUninitialize()
            
            # Mostrar resultado
            self.mostrar_resultado_envio(enviados_exitosos, errores, tipo_envio, resultado.get('modo_prueba', False))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error general en el envío:\n{e}")

    def crear_ventana_progreso(self, total_envios):
        """Crea ventana de progreso para el envío"""
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Enviando correos...")
        progress_win.geometry("400x150+400+300")
        progress_win.configure(bg='#f0f0f0')
        progress_win.grab_set()
        progress_win.resizable(False, False)
        
        tk.Label(progress_win, text="Enviando alertas...", 
                font=('Arial', 12, 'bold'), bg='#f0f0f0').pack(pady=20)
        
        progress_var = tk.StringVar(value="Preparando envío...")
        progress_label = tk.Label(progress_win, textvariable=progress_var, 
                                font=('Arial', 10), bg='#f0f0f0')
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_win, length=300, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['maximum'] = total_envios
        
        # Guardar referencias en la ventana
        progress_win.progress_var = progress_var
        progress_win.progress_bar = progress_bar
        
        progress_win.update()
        return progress_win

    def actualizar_progreso(self, progress_win, actual, total, mensaje):
        """Actualiza la barra de progreso"""
        try:
            progress_win.progress_var.set(f"{mensaje} ({actual}/{total})")
            progress_win.progress_bar['value'] = actual
            progress_win.update()
        except:
            pass  # Ventana puede haber sido cerrada

    def mostrar_resultado_envio(self, enviados, errores, tipo_envio, modo_prueba):
        """Muestra el resultado del envío"""
        total_intentos = enviados + len(errores)
        
        if errores:
            # Hay errores
            mensaje = f"Envío completado con errores:\n\n"
            mensaje += f"✅ Exitosos: {enviados}/{total_intentos}\n"
            mensaje += f"❌ Errores: {len(errores)}\n\n"
            mensaje += "Errores encontrados:\n" + "\n".join(errores[:3])
            if len(errores) > 3:
                mensaje += f"\n... y {len(errores)-3} errores más."
            
            messagebox.showwarning("Envío con errores", mensaje)
        else:
            # Todo exitoso
            modo_texto = " (MODO PRUEBA)" if modo_prueba else ""
            mensaje = f"¡Envío exitoso!{modo_texto}\n\n"
            mensaje += f"✅ {enviados} correo(s) enviado(s)\n"
            mensaje += f"📧 Alertas {tipo_envio} enviadas a los jefes correspondientes"
            
            messagebox.showinfo("✅ Envío exitoso", mensaje)

    def enviar_alertas_seleccionadas(self):
        """Envía reporte solo de las alertas seleccionadas"""
        alertas_seleccionadas = self.obtener_alertas_seleccionadas()
        
        if alertas_seleccionadas.empty:
            messagebox.showwarning("Sin selección", "Debe seleccionar al menos una alerta para enviar.\n\nTip: Mantenga Ctrl presionado para seleccionar múltiples filas.")
            return
        
        # Mostrar confirmación
        num_seleccionadas = len(alertas_seleccionadas)
        empleados = ", ".join(alertas_seleccionadas['Empleado'].tolist()[:3])  # Mostrar hasta 3 nombres
        if num_seleccionadas > 3:
            empleados += f" y {num_seleccionadas - 3} más"
        
        confirmar = messagebox.askyesno(
            "Confirmar envío",
            f"¿Enviar reporte con {num_seleccionadas} alerta(s) seleccionada(s)?\n\nEmpleados: {empleados}"
        )
        
        if not confirmar:
            return
        
        try:
            # Inicializar COM
            pythoncom.CoInitialize()
            
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = mail_test_gabriel
            #mail.CC = "bgacitua@cramer.cl"
            mail.Subject = f"Alertas de contratos seleccionadas - {datetime.now().strftime('%d/%m/%Y')}"

            # Generar HTML del reporte solo para seleccionadas
            html = self._generar_html_reporte_seleccionadas(alertas_seleccionadas)
            mail.HTMLBody = html
            mail.Send()

            pythoncom.CoUninitialize()
            messagebox.showinfo("✅ Enviado", f"Reporte con {num_seleccionadas} alerta(s) enviado a:\n• {mail_test_gabriel}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando correo:\n{e}")


    def cargar_alertas(self):
        """Carga las alertas y actualiza la interfaz"""
        self.alertas_df = self.obtener_alertas()
        
        # DEBUG: Para verificar las columnas (comentar después de corregir)
        if not self.alertas_df.empty:
            print("\n=== DEBUG INFO ===")
            print("Columnas disponibles:")
            for i, col in enumerate(self.alertas_df.columns):
                print(f"  {i}: '{col}'")
            print(f"\nTotal filas: {len(self.alertas_df)}")
            print("Muestra de datos:")
            print(self.alertas_df.head())
            print("==================\n")
        else:
            print("DataFrame vacío - No hay alertas o error en consulta")
        
        self.actualizar_metricas()
        self.actualizar_tabla()

        self.alertas_df = self.obtener_alertas()
        self.incidencias_df = self.obtener_incidencias()

    def actualizar_metricas(self):
        """Actualiza las métricas en la interfaz"""
        if self.alertas_df.empty:
            self.total_alertas_var.set("0")
            self.urgentes_var.set("0")
            self.requieren_accion_var.set("0")
            self.jefes_afectados_var.set("0")
        else:
            self.total_alertas_var.set(str(len(self.alertas_df)))
            self.urgentes_var.set(str((self.alertas_df["Urgente"] == 1).sum()))
            self.requieren_accion_var.set(str((self.alertas_df["Requiere Acción"] == 1).sum()))
            self.jefes_afectados_var.set(str(self.alertas_df["Jefe"].nunique()))

    def actualizar_tabla(self):
        """Actualiza la tabla de alertas"""
        # Limpiar tabla
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
                    row["Fecha inicio"],
                    row["Motivo"], 
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

    def _generar_html_para_jefe(self, jefe, email_jefe, alertas_jefe, modo_prueba=False):
        """Genera HTML personalizado para cada jefe"""
        modo_texto = "<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin-bottom: 20px; border-radius: 5px;'><strong>🧪 MODO PRUEBA:</strong> Este correo habría sido enviado a " + email_jefe + "</div>" if modo_prueba else ""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }}
                h2 {{ color: #e74c3c; }}
                .jefe-header {{ background-color: #3498db; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .alerta-container {{ border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
                .alerta-header {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; margin-bottom: 10px; }}
                .urgente {{ background-color: #fce4e4; border-left: 5px solid #e74c3c; }}
                .vencida {{ background-color: #ffcdd2; border-left: 5px solid #c62828; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; }}
                .resumen {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; margin-top: 30px; border-radius: 5px; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            {modo_texto}
            
            <div class="jefe-header">
                <h2>📋 Alertas de Contratos - {jefe}</h2>
                <p>Alertas pendientes para miembros de su equipo</p>
            </div>
            
            <div class="resumen">
                <h3>📊 Resumen</h3>
                <p><strong>Total de alertas:</strong> {len(alertas_jefe)}</p>
                <p><strong>Colaboradores afectados:</strong> {', '.join(alertas_jefe['Empleado'].tolist())}</p>
                <p><strong>Fecha de generación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>

            <p>Estimado/a <strong>{jefe}</strong>,</p>
            <p>Junto con saludar, le informamos que tiene <strong>{len(alertas_jefe)} alerta(s)</strong> de contratos pendientes de revisión en su equipo:</p>
        """

        # Agregar cada alerta del jefe
        for _, row in alertas_jefe.iterrows():
            dias_hasta = row["Días hasta alerta"]
            clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
            
            # Filtrar permisos para el empleado actual
            incidencias_empleado = self.incidencias_df[self.incidencias_df['rut_empleado'] == row['RUT']]
            
            html += f"""
            <div class="alerta-container {clase_css}">
                <div class="alerta-header">👤 {row['Empleado']} - {row['Cargo']}</div>
                <p><strong>Motivo:</strong> {row['Motivo']}</p>
                <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
                <p><strong>Días hasta la fecha:</strong> {dias_hasta} días</p>
            """
            
            # Tabla de permisos
            if not incidencias_empleado.empty:
                html += """
                <h4>📅 Permisos/Licencias Activas:</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Tipo de Permiso</th>
                            <th>Fecha de Inicio</th>
                            <th>Fecha de Fin</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for _, inc_row in incidencias_empleado.iterrows():
                    html += f"""
                        <tr>
                            <td>{inc_row['tipo_permiso']}</td>
                            <td>{inc_row['fecha_inicio']}</td>
                            <td>{inc_row['fecha_fin']}</td>
                        </tr>
                    """
                html += """
                    </tbody>
                </table>
                """
            else:
                html += "<p>✅ Este colaborador/a no registra ausencias, permisos y/o licencias activas.</p>"
                
            html += """
            </div>
            """

        html += f"""
            <div class="footer">
                <h4>📞 ¿Necesita ayuda?</h4>
                <p>Si tiene consultas sobre estas alertas o necesita apoyo para la renovación de contratos, 
                no dude en contactar al área de Recursos Humanos.</p>
                
                <p><strong>Equipo de Recursos Humanos</strong><br>
                📧 Email: {mail_test_gabriel}<br>
                📅 Sistema de Alertas de Contratos</p>
                
                <hr style="margin: 20px 0;">
                <p style="font-size: 0.8em; color: #666;">
                    <em>Este correo fue generado automáticamente por el Sistema de Alertas de Contratos de RRHH. 
                    Para consultas técnicas, contacte al administrador del sistema.</em>
                </p>
            </div>
        </body>
        </html>
        """
        return html

    def _generar_html_reporte_seleccionadas(self, alertas_seleccionadas):
        """Genera el HTML del reporte solo para las alertas seleccionadas"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #e74c3c; }}
                .alerta-container {{ border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
                .alerta-header {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; }}
                .urgente {{ background-color: #fce4e4; }}
                .vencida {{ background-color: #ffcdd2; }}
                .seleccionada {{ background-color: #e8f5e8; border-color: #27ae60; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; }}
                .resumen {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="resumen">
                <h3>Reporte Vencimiento de Contrato</h3>
            </div>
            
            <p>Estimado/a, junto con saludar</p>
            <p>Se adjunta el listado de colaboradores con contratos pendientes de revisión:</p>
        """

        # Bucle para crear una sección por cada alerta seleccionada
        for _, row in alertas_seleccionadas.iterrows():
            dias_hasta = row["Días hasta alerta"]
            clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
            clase_css += " seleccionada"  # Agregar clase para destacar que fue seleccionada
            
            # Filtrar permisos para el empleado actual
            incidencias_empleado = self.incidencias_df[self.incidencias_df['rut_empleado'] == row['RUT']]
            
            # HTML para la alerta del empleado
            html += f"""
            <div class="alerta-container {clase_css}">
                <div class="alerta-header">✅ Termino Contrato: {row['Empleado']}</div>
                <p><strong>Cargo:</strong> {row['Cargo']}</p>
                <p><strong>Motivo:</strong> {row['Motivo']}</p>
                <p><strong>Jefe Directo:</strong> {row['Jefe']} </p>
                <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
            """
            
            # HTML para la tabla de permisos
            if not incidencias_empleado.empty:
                html += """
                <h4>Permisos Activos:</h4>
                <table>
                    <thead>
                        <tr>
                            <th>Tipo de Permiso</th>
                            <th>Fecha de Inicio</th>
                            <th>Fecha de Fin</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for _, inc_row in incidencias_empleado.iterrows():
                    html += f"""
                        <tr>
                            <td>{inc_row['tipo_permiso']}</td>
                            <td>{inc_row['fecha_inicio']}</td>
                            <td>{inc_row['fecha_fin']}</td>
                        </tr>
                    """
                html += """
                    </tbody>
                </table>
                """
            else:
                html += "<p>Este colaborador/a no registra ausencias, permisos y/o licencias.</p>"
                
            html += """
            </div>
            """

        html += f"""
        <br>
        <div class="resumen">
            <p><strong>Resumen del envío:</strong></p>
            <ul>
                <li>Alertas seleccionadas: {len(alertas_seleccionadas)}</li>
                <li>Empleados: {', '.join(alertas_seleccionadas['Empleado'].tolist())}</li>
            </ul>
        </div>
        <p><em><strong>Generado automáticamente por el Sistema de Alertas de Contratos de RRHH</strong></em></p>
        </body>
        </html>
        """
        return html
    

    
    #-----------------------------------------------------------
    #               Ventana de resumen por jefe
    #-----------------------------------------------------------

    def mostrar_resumen_jefes(self):
        """Muestra ventana con resumen por jefe"""
        if self.alertas_df.empty:
            messagebox.showinfo("Sin datos", "No hay alertas para mostrar resumen.")
            return

        # Crear ventana de resumen
        resumen_win = tk.Toplevel(self.root)
        resumen_win.title("Resumen por Jefe")
        resumen_win.geometry("800x600+200+100")
        resumen_win.configure(bg='#f0f0f0')
        resumen_win.grab_set()

        # Título
        tk.Label(resumen_win, text="Resumen de Alertas por Jefe", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Crear treeview para resumen
        columns = ('Jefe', 'Email', 'Empleados Afectados') #'Total Alertas', 'Urgentes',
        resumen_tree = ttk.Treeview(resumen_win, columns=columns, show='headings', height=15)
        
        for col in columns:
            resumen_tree.heading(col, text=col)
            resumen_tree.column(col, width=150, anchor='w')

        # Calcular resumen por jefe
        resumen_jefes = self.alertas_df.groupby(['Jefe', 'Email Jefe']).agg({
            # 'ID': 'count',
            #'Urgente': 'sum',
            'Empleado': 'nunique'
        }).reset_index()

        # Llenar treeview
        for _, row in resumen_jefes.iterrows():
            resumen_tree.insert('', 'end', values=(
                row['Jefe'], row['Email Jefe'], row['Empleado']
            )) #row['ID'], row['Urgente'],

        resumen_tree.pack(fill='both', expand=True, padx=20, pady=10)

        # Botón cerrar
        tk.Button(resumen_win, text="Cerrar", command=resumen_win.destroy,
                 bg='#FF6961', fg='white', font=('Arial', 11, 'bold'),
                 relief='flat', padx=20, pady=10).pack(pady=15)

    def marcar_procesada(self):
        """Marca la alerta seleccionada como procesada"""
        seleccion = self.alertas_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una alerta para marcar como procesada.")
            return

        if messagebox.askyesno("Confirmar", "¿Marcar la alerta seleccionada como procesada?"):
            # Aquí implementarías la lógica para marcar en BD
            messagebox.showinfo("✅ Procesada", "Alerta marcada como procesada.")
            self.cargar_alertas()  # Recargar datos

#-----------------------------------------------------------
#                    Función Principal
#-----------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardAlertas(root)
    root.mainloop()