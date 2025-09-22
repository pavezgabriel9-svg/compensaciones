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
import win32com.client as win32
import pythoncom

#-----------------------------------------------------------
#                    Conexión BD
#-----------------------------------------------------------
# Entorno macOS
# DB_HOST = "localhost"
# DB_USER = "root"
# DB_PASSWORD = "cancionanimal"
# DB_NAME = "prueba_buk"

# Entorno Windows
DB_HOST = "192.168.245.33"
DB_USER = "compensaciones_rrhh"
DB_PASSWORD = "_Cramercomp2025_"
DB_NAME = "rrhh_app"

MAIL_TEST = "gpavez@cramer.cl"  

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
        self._crear_metrica(metrics_row, "Urgentes", self.urgentes_var, '#e74c3c')
        #self._crear_metrica(metrics_row, "Requieren Acción", self.requieren_accion_var, '#f39c12')
        self._crear_metrica(metrics_row, "Jefes Afectados", self.jefes_afectados_var, '#9b59b6')

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
                                   values=["Todos", "Urgentes", "Requieren Acción", "SEGUNDO_PLAZO", "INDEFINIDO"],
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
        columns = ('Empleado', 'Cargo', 'Jefe', 'Fecha inicio', 
                  'Motivo', 'Estado')
        
        self.alertas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configurar columnas
        anchos = [200, 150, 200, 120, 150, 100]
        for i, col in enumerate(columns):
            self.alertas_tree.heading(col, text=col)
            self.alertas_tree.column(col, width=anchos[i], anchor='w' if i < 5 else 'center')

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
        tk.Button(btn_frame, text="🔧 Enviar Reporte de Prueba", 
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
                    row["Empleado"], 
                    row["Cargo"], 
                    row["Jefe"], 
                    row["Fecha inicio"],
                    row["Motivo"], 
                    estado
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
        elif filtro == "Urgentes":
            return self.alertas_df[self.alertas_df["Urgente"] == 1]
        elif filtro == "Requieren Acción":
            return self.alertas_df[self.alertas_df["Requiere Acción"] == 1]
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
            mail.Subject = f"Reporte de alertas de contratos ({len(self.alertas_df)} pendientes)"

            # Generar HTML del reporte
            html = self._generar_html_reporte()
            mail.HTMLBody = html
            mail.Send()

            pythoncom.CoUninitialize()
            messagebox.showinfo("✅ Enviado", f"Reporte enviado a {MAIL_TEST}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando correo:\n{e}")


    def _generar_html_reporte(self):
        """Genera el HTML del reporte de alertas con detalles de permisos."""
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
                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #34495e; color: white; }}
            </style>
        </head>
        <body>
            <h2>Reporte de Alertas de Contratos</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Total alertas:</strong> {len(self.alertas_df)}</p>
        """

        # Bucle para crear una sección por cada alerta
        for _, row in self.alertas_df.iterrows():
            dias_hasta = row["Días hasta alerta"]
            clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
            
            # Filtrar permisos para el empleado actual
            incidencias_empleado = self.incidencias_df[self.incidencias_df['rut_empleado'] == row['RUT']]
            
            # HTML para la alerta del empleado
            html += f"""
            <div class="alerta-container {clase_css}">
                <div class="alerta-header">Termino Contrato: {row['Empleado']}</div>
                <p><strong>Cargo:</strong> {row['Cargo']}</p>
                <p><strong>Motivo:</strong> {row['Motivo']}</p>
                <p><strong>Jefe:</strong> {row['Jefe']} ({row['Email Jefe']})</p>
                <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
                <!-- <p><strong>Estado:</strong> {'🔴 VENCIDA' if dias_hasta <= 0 else '🟠 URGENTE' if row['Urgente'] == 1 else '🟡 ACCIÓN'}</p> -->
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
                html += "<p>Este empleado no registra ausencias, permisos y/o licencias.</p>"
                
            html += """
            </div>
            """

        html += """
        <br>
        <p><em>Generado automáticamente por el Sistema de Alertas de Contratos de RRHH</em></p>
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
        resumen_win.title("💼 Resumen por Jefe")
        resumen_win.geometry("800x600+200+100")
        resumen_win.configure(bg='#f0f0f0')
        resumen_win.grab_set()

        # Título
        tk.Label(resumen_win, text="💼 Resumen de Alertas por Jefe", 
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
        tk.Button(resumen_win, text="⌐ Cerrar", command=resumen_win.destroy,
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