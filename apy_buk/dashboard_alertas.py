#-----------------------------------------------------------
#                           Importaciones
#-----------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

#envio de correos por outlook
#import win32com.client as win32
#import pythoncom envio de 

#-----------------------------------------------------------
#                    Conexión BD
#-----------------------------------------------------------
# Entorno macOS
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "cancionanimal"
DB_NAME = "prueba_buk"

# Entorno Windows
# DB_HOST = "10.254.33.138"
# DB_USER = "compensaciones_rrhh"
# DB_PASSWORD = "_Cramercomp2025_"
# DB_NAME = "rrhh_app"

# MAIL_TEST = "gpavez@cramer.cl"  

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
        self.root.title("Alertas de Contratos")
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
        """Obtiene las alertas desde la base de datos"""
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
                days_since_start,
                DATEDIFF(alert_date, CURDATE()) as dias_hasta_alerta,
                is_urgent, requires_action, alert_type
            FROM contract_alerts 
            WHERE processed = FALSE
            ORDER BY alert_date ASC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            cols = ["ID", "Empleado", "RUT", "Cargo", "Área", "Jefe", "Email Jefe",
                    "Fecha alerta", "Motivo", "Días desde inicio",
                    "Días hasta alerta", "Urgente", "Requiere Acción", "Tipo Alerta"]
            
            df = pd.DataFrame(rows, columns=cols)
            cursor.close()
            conexion.close()
            return df
            
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo alertas:\n{e}")
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
        metrics_frame = tk.LabelFrame(parent, text="📈 Resumen de Alertas", 
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
        self._crear_metrica(metrics_row, "🚨 Urgentes", self.urgentes_var, '#e74c3c')
        self._crear_metrica(metrics_row, "⏰ Requieren Acción", self.requieren_accion_var, '#f39c12')
        self._crear_metrica(metrics_row, "👔 Jefes Afectados", self.jefes_afectados_var, '#9b59b6')

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
        tabla_frame = tk.LabelFrame(parent, text="📋 Detalle de Alertas", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        tabla_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Frame para filtros
        filtros_frame = tk.Frame(tabla_frame, bg='#f0f0f0')
        filtros_frame.pack(fill='x', pady=(0, 10))

        tk.Label(filtros_frame, text="Filtrar por:", font=('Arial', 10), bg='#f0f0f0').pack(side='left', padx=5)
        
        self.filtro_var = tk.StringVar(value="Todos")
        filtro_combo = ttk.Combobox(filtros_frame, textvariable=self.filtro_var, 
                                   values=["Todos", "VENCIDA", "URGENTE","FUTURA", "SEGUNDO_PLAZO", "INDEFINIDO"],
                                   state="readonly", width=15)
        filtro_combo.pack(side='left', padx=5)
        filtro_combo.bind('<<ComboboxSelected>>', self.aplicar_filtro)

        tk.Button(filtros_frame, text="🔄 Actualizar", command=self.cargar_alertas,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'), 
                 relief='flat', padx=10, pady=5).pack(side='right', padx=5)

        # Crear Treeview
        self._crear_treeview_alertas(tabla_frame)

    def _crear_treeview_alertas(self, parent):
        """Crea el treeview para mostrar alertas"""
        # Frame para treeview y scrollbar
        tree_frame = tk.Frame(parent, bg='#f0f0f0')
        tree_frame.pack(fill='both', expand=True)

        # Columnas
        columns = ('Empleado', 'Cargo', 'Jefe', 'Fecha Alerta', 
                  'Motivo', 'Días hasta alerta', 'Estado')
                    #'Área', 'RUT', 
        
        self.alertas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        anchos = [150, 100, 120, 60, 120, 50, 50]
        for i, col in enumerate(columns):
            self.alertas_tree.heading(col, text=col)
            if col in ['Fecha Alerta', 'Días hasta alerta', 'Estado']:
                self.alertas_tree.column(col, width=anchos[i], anchor='center')
            else:
                self.alertas_tree.column(col, width=anchos[i], anchor='w')

        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=self.alertas_tree.yview)
        scrollbar_h = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.alertas_tree.xview)
        self.alertas_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        # Pack
        self.alertas_tree.pack(side='left', fill='both', expand=True)
        scrollbar_v.pack(side='right', fill='y')
        scrollbar_h.pack(side='bottom', fill='x')

    def crear_seccion_acciones(self, parent):
        """Crea la sección de acciones"""
        acciones_frame = tk.LabelFrame(parent, text="🚀 Acciones", 
                                      font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                      padx=15, pady=15)
        acciones_frame.pack(fill='x')

        # Frame para botones
        btn_frame = tk.Frame(acciones_frame, bg='#f0f0f0')
        btn_frame.pack()

        # Botones principales
        tk.Button(btn_frame, text="📧 Enviar Reporte de Prueba", 
                 command=self.enviar_reporte_prueba,
                 bg='#e67e22', fg='white', font=('Arial', 11, 'bold'), 
                 relief='flat', padx=20, pady=10).pack(side='left', padx=10)

        tk.Button(btn_frame, text="📊 Ver Resumen por Jefe", 
                 command=self.mostrar_resumen_jefes,
                 bg='#9b59b6', fg='white', font=('Arial', 11, 'bold'), 
                 relief='flat', padx=20, pady=10).pack(side='left', padx=10)

        tk.Button(btn_frame, text="✅ Marcar como Procesada", 
                 command=self.marcar_procesada,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'), 
                 relief='flat', padx=20, pady=10).pack(side='left', padx=10)

    def cargar_alertas(self):
        """Carga las alertas y actualiza la interfaz"""
        self.alertas_df = self.obtener_alertas()
        self.actualizar_metricas()
        self.actualizar_tabla()

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
            # Determinar estado visual
            dias_hasta = row["Días hasta alerta"]
            if dias_hasta <= 0:
                estado = "VENCIDA"
            elif row["Urgente"] == 1:
                estado = "URGENTE"
            elif row["Requiere Acción"] == 1:
                estado = "ACCIÓN"
            else:
                estado = "FUTURA"

            valores = (
                row["Empleado"], row["Cargo"],
                row["Jefe"], row["Fecha alerta"], row["Motivo"], 
                str(dias_hasta), estado
            ) # row["Área"], row["RUT"], 
            
            item = self.alertas_tree.insert('', 'end', values=valores)
            
            # Colorear filas según urgencia
            if dias_hasta <= 0:
                self.alertas_tree.set(item, 'Estado', 'VENCIDA')
            elif row["Urgente"] == 1:
                self.alertas_tree.set(item, 'Estado', 'URGENTE')

    def aplicar_filtro_actual(self):
        """Aplica el filtro seleccionado"""
        if self.alertas_df.empty:
            return self.alertas_df

        filtro = self.filtro_var.get()
        
        if filtro == "Todos":
            return self.alertas_df
        elif filtro == "VENCIDA":
            return self.alertas_df[self.alertas_df["VENCIDA"] == 1]
        elif filtro == "URGENTE":
            return self.alertas_df[self.alertas_df["URGENTE"] == 1]
        elif filtro == "FUTURA":
            return self.alertas_df[self.alertas_df["FUTURA"] == 1]
        elif filtro in ["SEGUNDO_PLAZO", "INDEFINIDO"]:
            return self.alertas_df[self.alertas_df["Tipo Alerta"] == filtro]
        else:
            return self.alertas_df

    def aplicar_filtro(self, event=None):
        """Aplica filtro cuando cambia la selección"""
        self.actualizar_tabla()

    def enviar_reporte_prueba(self):
        """Envía reporte de prueba a tu correo"""
        if self.alertas_df.empty:
            messagebox.showwarning("Sin datos", "No hay alertas activas para enviar.")
            return

        try:
            # Inicializar COM
            pythoncom.CoInitialize()
            
            outlook = win32.Dispatch("outlook.application")
            mail = outlook.CreateItem(0)
            mail.To = MAIL_TEST
            mail.Subject = f"🚨 Reporte de alertas de contratos ({len(self.alertas_df)} pendientes)"

            # Generar HTML del reporte
            html = self._generar_html_reporte()
            mail.HTMLBody = html
            mail.Send()

            pythoncom.CoUninitialize()
            messagebox.showinfo("✅ Enviado", f"Reporte enviado a {MAIL_TEST}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando correo:\n{e}")

    def _generar_html_reporte(self):
        """Genera el HTML del reporte de alertas"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #e74c3c; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th {{ background-color: #34495e; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .urgente {{ background-color: #ffebee; }}
                .vencida {{ background-color: #ffcdd2; }}
            </style>
        </head>
        <body>
            <h2>📊 Reporte de Alertas de Contratos</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Total alertas:</strong> {len(self.alertas_df)}</p>
            
            <table>
                <tr>
                    <th>Empleado</th>
                    <th>RUT</th>
                    <th>Cargo</th>
                    <th>Área</th>
                    <th>Jefe</th>
                    <th>Fecha Alerta</th>
                    <th>Motivo</th>
                    <th>Días hasta alerta</th>
                    <th>Estado</th>
                </tr>
        """
        
        for _, row in self.alertas_df.iterrows():
            dias_hasta = row["Días hasta alerta"]
            clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
            
            html += f"""
                <tr class="{clase_css}">
                    <td>{row['Empleado']}</td>
                    <td>{row['RUT']}</td>
                    <td>{row['Cargo']}</td>
                    <td>{row['Área']}</td>
                    <td>{row['Jefe']}</td>
                    <td>{row['Fecha alerta']}</td>
                    <td>{row['Motivo']}</td>
                    <td>{dias_hasta}</td>
                    <td>{'🔴 VENCIDA' if dias_hasta <= 0 else '🟠 URGENTE' if row['Urgente'] == 1 else '🟡 ACCIÓN'}</td>
                </tr>
            """
        
        html += """
            </table>
            <br>
            <p><em>Generado automáticamente por el Sistema de Alertas de Contratos</em></p>
        </body>
        </html>
        """
        return html

    def mostrar_resumen_jefes(self):
        """Muestra ventana con resumen por jefe"""
        if self.alertas_df.empty:
            messagebox.showinfo("Sin datos", "No hay alertas para mostrar resumen.")
            return

        # Crear ventana de resumen
        resumen_win = tk.Toplevel(self.root)
        resumen_win.title("👔 Resumen por Jefe")
        resumen_win.geometry("800x600+200+100")
        resumen_win.configure(bg='#f0f0f0')
        resumen_win.grab_set()

        # Título
        tk.Label(resumen_win, text="👔 Resumen de Alertas por Jefe", 
                font=('Arial', 14, 'bold'), bg='#f0f0f0', fg='#2c3e50').pack(pady=15)

        # Crear treeview para resumen
        columns = ('Jefe', 'Email', 'Total Alertas', 'Urgentes', 'Empleados Afectados')
        resumen_tree = ttk.Treeview(resumen_win, columns=columns, show='headings', height=15)
        
        for col in columns:
            resumen_tree.heading(col, text=col)
            resumen_tree.column(col, width=150, anchor='w')

        # Calcular resumen por jefe
        resumen_jefes = self.alertas_df.groupby(['Jefe', 'Email Jefe']).agg({
            'ID': 'count',
            'Urgente': 'sum',
            'Empleado': 'nunique'
        }).reset_index()

        # Llenar treeview
        for _, row in resumen_jefes.iterrows():
            resumen_tree.insert('', 'end', values=(
                row['Jefe'], row['Email Jefe'], row['ID'], 
                row['Urgente'], row['Empleado']
            ))

        resumen_tree.pack(fill='both', expand=True, padx=20, pady=10)

        # Botón cerrar
        tk.Button(resumen_win, text="❌ Cerrar", command=resumen_win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11, 'bold'),
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