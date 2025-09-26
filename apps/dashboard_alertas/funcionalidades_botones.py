import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd


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
            
def enviar_a_todos_los_jefes():
        """Envía todas las alertas a los jefes correspondientes"""
        if alertas_df.empty:
            messagebox.showwarning("Sin datos", "No hay alertas activas para enviar.")
            return
        
        # Agrupar todas las alertas por jefe
        alertas_por_jefe = alertas_df.groupby(['Jefe', 'Email Jefe'])
        num_jefes = len(alertas_por_jefe)
        num_alertas = len(alertas_df)
        
        # Mostrar ventana de confirmación
        if mostrar_confirmacion_envio(alertas_por_jefe, num_jefes, num_alertas, "todas"):
            procesar_envio_a_jefes(alertas_por_jefe, "todas")
            
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
            html_reporte = generar_html_reporte_seleccionadas(
                alertas_seleccionadas=alertas_seleccionadas,
                incidencias_df=self.incidencias_df
            )


            mail.HTMLBody = html_reporte
            mail.Send()

            pythoncom.CoUninitialize()
            messagebox.showinfo("✅ Enviado", f"Reporte con {num_seleccionadas} alerta(s) enviado a:\n• {mail_test_gabriel}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error enviando correo:\n{e}")
            
def mostrar_resumen_jefes():
    """Muestra ventana con resumen por jefe"""
    if alertas_df.empty:
        messagebox.showinfo("Sin datos", "No hay alertas para mostrar resumen.")
        return

    # Crear ventana de resumen
    resumen_win = tk.Toplevel(root)
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
    resumen_jefes = alertas_df.groupby(['Jefe', 'Email Jefe']).agg({
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

def marcar_procesada():
        """Marca la alerta seleccionada como procesada"""
        seleccion = alertas_tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una alerta para marcar como procesada.")
            return

        if messagebox.askyesno("Confirmar", "¿Marcar la alerta seleccionada como procesada?"):
            # Aquí implementarías la lógica para marcar en BD
            messagebox.showinfo("✅ Procesada", "Alerta marcada como procesada.")
            cargar_alertas()  # Recargar datos