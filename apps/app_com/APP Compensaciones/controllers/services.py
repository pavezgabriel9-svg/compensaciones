# services.py

import datetime
import pandas as pd
from databases import request_db
from views.personal_file_view import PersonalFileView

def cargar_datos_ventana_principal(app):
    """
    CARGA LOS DATOS NECESARIOS PARA LA VENTANA PRINCIPAL 
    """
    df_main = request_db.obtener_datos()
    df_settlements = request_db.obtener_datos_liquidaciones()
    df_employees = request_db.obtener_datos_empleados()
    
    if df_main is not None and not df_main.empty:
        try:
            app.data_df = df_main
            app.settlements_df = df_settlements
            app.employees_df = df_employees

            actualizar_dashboard(app, app.data_df)

            empresa = sorted(app.data_df["company_name"].dropna().unique())
            division = sorted(app.data_df["division_name"].dropna().unique())
            areas = sorted(app.data_df["area_name"].dropna().unique())
            
            app.filtro_empresa['values'] = ["Todos"] + empresa
            app.filtro_division['values'] = ["Todos"] + division
            app.filtro_areas['values'] = ["Todos"] + areas   
        
            print("Todos los datos han sido cargados exitosamente.")
        except Exception as e:
            print(f"No se pudieron cargar los datos en la ventana principal: {e}")

                
def actualizar_dashboard(app, df):
    """
    ACTUALIZA LOS DATOS DEL DASHBOARD 
    """
    if df is None or df.empty:
        print("Sin datos", "No se encontraron datos para mostrar en el dashboard.")
        return
    
    actualizar_metricas(app)
    actualizar_tabla(app)

def actualizar_metricas(app):
    """
    ACTUALIZA LAS MÉTRICAS DEL DASHBOARD
    """
    df_para_metricas = getattr(app, 'df_filtrado', app.data_df)
    
    if df_para_metricas.empty:
        total_empleados = 0
        promedio_base = 0
        promedio_anios = 0
    else:
        total_empleados = len(df_para_metricas["rut"].unique())
        promedio_base = round(df_para_metricas["base_wage"].mean(), 0)
        promedio_anios = round(df_para_metricas["service_years"].mean(), 1)

    app.total_empleados.set(str(total_empleados))
    app.promedio_base.set(f"${promedio_base:,.0f}")
    app.promedio_anios.set(f"{promedio_anios} años") 
    
def actualizar_tabla(app):
    """
    ACTUALIZA LA TABLA DE EMPLEADOS CON LOS FILTROS APLICADOS
    """
    if not hasattr(app, 'data_df') or app.data_df.empty:
        return
    
    for item in app.tree.get_children():
        app.tree.delete(item)

    df_ultimo = app.data_df.sort_values(["person_id", "years", "month"]).groupby("person_id").tail(1)
    app.df_filtrado = aplicar_filtros(app, df_ultimo)
    actualizar_metricas(app)
    
    for _, row in app.df_filtrado.iterrows():
        sueldo_actual = f"${row['base_wage']:,.0f}" if pd.notna(row.get('base_wage')) else "N/A"
        jefatura = row.get('boss_name', 'N/A') if pd.notna(row.get('boss_name')) else "N/A"
        cargo = row.get('role_name', 'N/A')
        anos_servicio = f"{row.get('service_years', 0):.1f}"
        nivel = row.get('level', 'N/A') 

        app.tree.insert("", "end", values=(
            row.get("rut", ""),
            row.get("full_name", ""),
            cargo,
            jefatura,
            sueldo_actual,
            nivel,
            anos_servicio
        ))
   
def aplicar_filtros(app, df):
    df_filtrado = df.copy()
    search_term = app.busqueda_nombre.get().strip()
    
    # FILTRO POR EMPRESA
    empresa_seleccionada = app.empresa_var.get()
    if empresa_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["company_name"] == empresa_seleccionada]
        
    # FILTRO POR DIVISION
    division_seleccionada = app.division_var.get()
    if division_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["division_name"] == division_seleccionada]
    
    # FILTRO POR AREA
    area_seleccionada = app.area_var.get()
    if area_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado["area_name"] == area_seleccionada]
        
    
    # BUSQUEDA POR NOMBRE O RUT
    if search_term:
        palabras = search_term.lower().split()
        mask_nombre = df_filtrado["full_name"].str.lower().apply(lambda x: all(p in x for p in palabras) if isinstance(x, str) else False)
        mask_rut = df_filtrado["rut"].str.contains(search_term, case=False, na=False)
        df_filtrado = df_filtrado[mask_nombre | mask_rut]
        
    # BUSQUEDA POR CARGO
    search_cargo_term = app.search_cargo_var.get().strip()
    if search_cargo_term:
        df_filtrado = df_filtrado[df_filtrado["role_name"].str.contains(search_cargo_term, case=False, na=False)]
        
    # BUSQUEDA POR JEFATURA
    search_jefatura_term = app.search_jefatura_var.get().strip()
    if search_jefatura_term:
        df_filtrado = df_filtrado[df_filtrado["boss_name"].str.contains(search_jefatura_term, case=False, na=False)]
            
    return df_filtrado
    
def limpiar_filtros(app):
    """Limpia todos los filtros y actualiza la tabla"""
    app.empresa_var.set("Todos")
    app.division_var.set("Todos")
    app.area_var.set("Todos")
    app.busqueda_nombre.set("")
    app.search_cargo_var.set("")
    app.search_jefatura_var.set("")

    actualizar_tabla(app)


def abrir_ficha_persona(app):
    """
    Manejador del evento de doble clic en la tabla principal.
    Obtiene el RUT y abre la ventana de la ficha personal.
    """
    try:
        selected_item = app.tree.focus()
        if not selected_item:
            return
        
        item_values = app.tree.item(selected_item, "values")
        if not item_values:
            return

        rut_seleccionado = item_values[0]
    
        ficha_window = PersonalFileView(
        parent=app.root, 
        rut=rut_seleccionado,
        data_df=app.data_df,
        employees_df=app.employees_df, 
        settlements_df=app.settlements_df
    )
        ficha_window.mainloop()

    except Exception as e:
        print(f"Error al abrir la ficha personal: {e}")

        
