"""
Procesos del dashboard de alertas vinculados a DF's
"""

import pandas as pd
from db_utils import obtener_alertas, obtener_incidencias
from tkinter import ttk, messagebox as tk
from design_dashboard import crear_seccion_metricas


# selección multiple
def crear_treeview_alertas(parent):
    """Crea el treeview para mostrar alertas con selección múltiple habilitada"""
    # Frame para treeview y scrollbar
    tree_frame = tk.Frame(parent, bg='#f0f0f0')
    tree_frame.pack(fill='both', expand=True)

    # Columnas
    columns = ('Empleado', 'Cargo', 'Jefe', 'Fecha inicio', 'Motivo')
    
    alertas_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                    height=15, selectmode='extended')
    
    # Configurar columnas
    anchos = [200, 150, 200, 120, 150]
    for i, col in enumerate(columns):
        alertas_tree.heading(col, text=col)
        alertas_tree.column(col, width=anchos[i], anchor='w')

    # Scrollbars
    scrollbar_v = ttk.Scrollbar(tree_frame, orient='vertical', command=alertas_tree.yview)
    alertas_tree.configure(yscrollcommand=scrollbar_v.set)

    # Pack
    alertas_tree.pack(side='left', fill='both', expand=True)
    scrollbar_v.pack(side='right', fill='y')
    
    return alertas_tree

def crear_seccion_tabla(parent):
        """Crea la sección de tabla de alertas"""
        tabla_frame = tk.LabelFrame(parent, text="Alertas", 
                                   font=('Arial', 12, 'bold'), bg='#f0f0f0', fg='#2c3e50', 
                                   padx=10, pady=10)
        tabla_frame.pack(fill='both', expand=True, pady=(0, 10))

        # Frame para filtros
        filtros_frame = tk.Frame(tabla_frame, bg='#f0f0f0')
        filtros_frame.pack(fill='x', pady=(0, 10))

        tk.Label(filtros_frame, text="Filtrar por:", font=('Arial', 10), bg='#f0f0f0').pack(side='left', padx=5)
        
        filtro_var = tk.StringVar(value="Todos")
        filtro_combo = ttk.Combobox(filtros_frame, textvariable=filtro_var, 
                                   values=["Todos", "SEGUNDO_PLAZO", "INDEFINIDO"],
                                   state="readonly", width=15)
        filtro_combo.pack(side='left', padx=5)
        
        filtro_combo.bind('<<ComboboxSelected>>', aplicar_filtro)

        tk.Button(filtros_frame, text="Actualizar", command=cargar_alertas,
                 bg='#27ae60', fg='white', font=('Arial', 9, 'bold'), 
                 relief='flat', padx=10, pady=5).pack(side='right', padx=5)

        # Crear Treeview
        tree = crear_treeview_alertas(tabla_frame)
        return tree, filtro_var
 
def aplicar_filtro_actual(alertas_df, filtro_var):
    """Aplica el filtro seleccionado"""
    if alertas_df.empty:
        return alertas_df

    filtro = filtro_var.get()
    
    if filtro == "Todos":
        return alertas_df
    elif filtro in ["SEGUNDO_PLAZO", "INDEFINIDO"]:
        return alertas_df[alertas_df["Tipo Alerta"] == filtro]
    else:
        return alertas_df

def actualizar_metricas(alertas_df, metricas):
    if alertas_df.empty:
        for var in metricas.values():
            var.set("0")
    else:
        metricas["total_alertas"].set(str(len(alertas_df)))
        metricas["urgentes"].set(str((alertas_df["Urgente"] == 1).sum()))
        metricas["requieren_accion"].set(str((alertas_df["Requiere Acción"] == 1).sum()))
        metricas["jefes_afectados"].set(str(alertas_df["Jefe"].nunique()))


            
def cargar_alertas():
    """Carga las alertas y actualiza la interfaz"""
    alertas_df = obtener_alertas()
    
    # DEBUG: Para verificar las columnas
    if not alertas_df.empty:
        print("\n=== DEBUG INFO ===")
        print("Columnas disponibles:")
        for i, col in enumerate(alertas_df.columns):
            print(f"  {i}: '{col}'")
        print(f"\nTotal filas: {len(alertas_df)}")
        print("Muestra de datos:")
        print(alertas_df.head())
        print("==================\n")
    else:
        print("DataFrame vacío - No hay alertas o error en consulta")
    
    actualizar_metricas()
    actualizar_tabla()

    incidencias_df = obtener_incidencias()
    return alertas_df, incidencias_df

def aplicar_filtro(event=None):
        """Aplica filtro cuando cambia la selección"""
        actualizar_tabla()
        
def actualizar_tabla(alertas_tree, alertas_df):
        """Actualiza la tabla de alertas"""
        # Limpiar tabla
        for item in alertas_tree.get_children():
            alertas_tree.delete(item)

        if alertas_df.empty:
            return

        # Aplicar filtro actual
        df_filtrado = aplicar_filtro_actual()

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
                item = alertas_tree.insert('', 'end', values=valores)
                
            except KeyError as e:
                print(f"Error accediendo a columna: {e}")
                print(f"Columnas disponibles: {list(row.index)}")
                break
            except Exception as e:
                print(f"Error general en fila: {e}")
                continue 
            
            
            
            
