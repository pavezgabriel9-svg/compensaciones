from views.main_ui import ConfigUI
from controllers import services 

def main():
    app = ConfigUI()
    services.cargar_datos_ventana_principal(app)
    
    app.run()

if __name__ == "__main__":
    main()
