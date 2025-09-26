# UI
import tkinter as tk
from tkinter import ttk, messagebox
from funcionalidades_botones import enviar_a_jefes_seleccionadas, enviar_a_todos_los_jefes, enviar_alertas_seleccionadas,mostrar_resumen_jefes,marcar_procesada
from process_pd import *


def setup_ui(root):
    """Configura la interfaz de usuario"""
    configurar_ventana_principal(root)
    crear_titulo(root)
    
    # Frame principal
    main_frame = tk.Frame(bg='#f0f0f0')
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    crear_seccion_metricas(main_frame)
    crear_seccion_tabla(main_frame)
    crear_seccion_acciones(main_frame)
    
    return main_frame
    
        
def configurar_ventana_principal(root):
        """Configura la ventana principal"""
        root.title("Alertas de Contratos")
        root.minsize(1200, 700)
        root.geometry("1300x800+50+50")
        root.configure(bg='#f0f0f0')


def crear_titulo(root):
        """Crea el título de la aplicación"""
        root.title_frame = tk.Frame(root, bg='#e74c3c', height=60)
        root.title_frame.pack(fill='x')
        root.title_frame.pack_propagate(False)
        
        title_label = tk.Label(root.title_frame, text="Alertas de Contratos", 
                              font=('Arial', 16, 'bold'), fg='white', bg='#e74c3c')
        title_label.pack(expand=True, pady=15)
        

def crear_seccion_metricas(parent):
    """Crea la sección de métricas principales"""
    metrics_frame = tk.LabelFrame(parent, text="Resumen de Alertas", 
                                    font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                    padx=15, pady=15)
    metrics_frame.pack(fill='x', pady=(0, 10))

    # Frame para métricas en fila
    metrics_row = tk.Frame(metrics_frame, bg='#f0f0f0')
    metrics_row.pack(fill='x')

    # Variables para métricas
    metricas = {
        "total_alertas_var" : tk.StringVar(value="0"),
        "urgentes_var" : tk.StringVar(value="0"),
        "requieren_accion_var" : tk.StringVar(value="0"),
        "jefes_afectados_var" : tk.StringVar(value="0")
    }

    # Crear métricas
    crear_metrica(metrics_row, "Total Alertas", metricas["total_alertas_var"], '#3498db')
    crear_metrica(metrics_row, "Jefes por Notificar", ["jefes_afectados_var"], '#9b59b6')
    
    return metricas
    
        
  
        
def crear_metrica(parent, titulo, variable, color):
        """Crea una métrica individual"""
        metric_frame = tk.Frame(parent, bg=color, relief='raised', bd=2)
        metric_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)

        tk.Label(metric_frame, text=titulo, font=('Arial', 10, 'bold'), 
                fg='white', bg=color).pack(pady=(10, 5))
        
        tk.Label(metric_frame, textvariable=variable, font=('Arial', 18, 'bold'), 
                fg='white', bg=color).pack(pady=(0, 10))
        
        
def crear_seccion_acciones(parent):
        """Crea la sección de acciones"""
        acciones_frame = tk.LabelFrame(parent, text="Acciones", 
                                    font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                    padx=15, pady=15)
        acciones_frame.pack(fill='x')

        # Frame para botones - Primera fila
        btn_frame1 = tk.Frame(acciones_frame, bg='#f0f0f0')
        btn_frame1.pack(pady=(0, 5))

        btn1 = tk.Button(btn_frame1, text="Enviar Alertas Seleccionadas", 
            command=enviar_a_jefes_seleccionadas,  
            bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'), 
            relief='flat', padx=20, pady=10)
        btn1.pack(side='left', padx=5)

        btn2 = tk.Button(btn_frame1, text="Enviar Todas las Alertas", 
                command=enviar_a_todos_los_jefes, 
                bg='#c0392b', fg='white', font=('Arial', 11, 'bold'), 
                relief='flat', padx=20, pady=10)
        btn2.pack(side='left', padx=5)

    # Frame para botones - Segunda fila
        btn_frame2 = tk.Frame(acciones_frame, bg='#f0f0f0')
        btn_frame2.pack(pady=(5, 0))

        btn3 = tk.Button(btn_frame2, text="Reporte Test (Seleccionadas)",
                command=enviar_alertas_seleccionadas, 
                bg='#95a5a6', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8)
        btn3.pack(side='left', padx=5)

        btn4 = tk.Button(btn_frame2, text="Resumen por Jefe",
                command=mostrar_resumen_jefes, 
                bg='#9b59b6', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8)
        btn4.pack(side='left', padx=5)

        btn5 = tk.Button(btn_frame2, text="Marcar como Procesada",
                command=marcar_procesada, 
                bg='#27ae60', fg='white', font=('Arial', 10), 
                relief='flat', padx=15, pady=8)
        btn5.pack(side='left', padx=5)
    
        return {
        'btn_enviar_seleccionadas': btn1,
        'btn_enviar_todas': btn2,
        'btn_reporte_test': btn3,
        'btn_resumen_jefes': btn4,
        'btn_marcar_procesada': btn5
        }
        


        
