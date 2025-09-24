#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Compensaciones
Punto principal de la aplicación
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def resource_path(relative_path):
    """
    Obtiene la ruta correcta para recursos empaquetados con PyInstaller
    """
    try:
        # PyInstaller crea una carpeta temp y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def setup_paths():
    """
    Configura las rutas necesarias para el funcionamiento de la aplicación
    """
    # Agregar el directorio actual al path para imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

def check_dependencies():
    """
    Verifica que las dependencias críticas estén disponibles
    """
    required_modules = [
        'tkinter',
        'pymysql', 
        'pandas',
        'matplotlib'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        error_msg = f"Módulos faltantes: {', '.join(missing_modules)}"
        logging.error(error_msg)
        messagebox.showerror("Error de Dependencias", error_msg)
        return False
    
    return True

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Maneja excepciones no capturadas
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = f"Error no manejado: {exc_type.__name__}: {exc_value}"
    logging.error(error_msg, exc_info=(exc_type, exc_value, exc_traceback))
    
    # Mostrar error al usuario si hay interfaz gráfica disponible
    try:
        messagebox.showerror(
            "Error Crítico", 
            f"Ha ocurrido un error inesperado:\n\n{error_msg}\n\nRevisa el archivo dashboard.log para más detalles."
        )
    except:
        pass  # Si no hay interfaz gráfica disponible, solo logear

def main():
    """
    Función principal de la aplicación
    """
    try:
        # Configurar manejo de excepciones
        sys.excepthook = handle_exception
        
        # Configurar rutas
        setup_paths()
        
        # Verificar dependencias
        if not check_dependencies():
            return 1
        
        # Importar después de verificar dependencias
        from controllers.main_controller import MainController
        
        logging.info("Iniciando Dashboard de Compensaciones...")
        
        # Crear ventana principal
        root = tk.Tk()
        
        # Configuraciones básicas de la ventana principal
        root.title("Dashboard de Compensaciones")
        root.minsize(1300, 750)
        
        # Centrar ventana en pantalla
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Inicializar controlador principal
        try:
            controller = MainController(root)
            controller.initialize()
        except Exception as e:
            logging.error(f"Error inicializando controlador: {e}")
            messagebox.showerror(
                "Error de Inicialización",
                f"No se pudo inicializar la aplicación:\n{e}"
            )
            return 1
        
        # Manejar cierre de ventana
        def on_closing():
            try:
                controller.cleanup()  # Cerrar conexiones, limpiar recursos
                logging.info("Aplicación cerrada correctamente")
            except Exception as e:
                logging.error(f"Error durante el cierre: {e}")
            finally:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Iniciar loop principal
        logging.info("Aplicación iniciada correctamente")
        root.mainloop()
        
        return 0
        
    except Exception as e:
        logging.error(f"Error crítico en main: {e}", exc_info=True)
        try:
            messagebox.showerror(
                "Error Crítico", 
                f"Error crítico al iniciar la aplicación:\n{e}"
            )
        except:
            print(f"Error crítico: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)