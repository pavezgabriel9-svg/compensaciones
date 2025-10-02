from UI.ui import ConfigUI
from SERVICE import services

def main():
    app = ConfigUI()
    app.formato_chile_sueldo_callback = services.formato_chile_sueldo
    app.run()

if __name__ == "__main__":
    main()