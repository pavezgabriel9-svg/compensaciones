from interfaz_usuario.ui import ConfigUI
from procesamientos import services

def main():
    app = ConfigUI()
    
    app.enviar_selecionada_callback = lambda: services.enviar_alertas_seleccionadas(app)
    app.actualizar_callback = lambda: services.cargar_alertas(app)
    app.enviar_seleccionadas_por_jefe_callback = lambda jefes_filtro: services.enviar_alertas_seleccionadas_por_jefe(app, jefes_filtro)
    
    if app.actualizar_callback:
        app.actualizar_callback()
    
    app.run()

if __name__ == "__main__":
    main()
