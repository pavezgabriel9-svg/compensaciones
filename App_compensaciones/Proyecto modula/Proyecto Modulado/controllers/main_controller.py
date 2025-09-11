# controllers/main_controller.py
"""
Controlador principal que coordina toda la aplicación
"""

import tkinter as tk
from tkinter import messagebox
import logging

from views.main_window import MainWindow
from models.database_manager import DatabaseManager
from controllers.dashboard_controller import DashboardController
from controllers.group_controller import GroupController

class MainController:
    """
    Controlador principal que coordina todos los componentes de la aplicación
    """
    
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(__name__)
        
        # Componentes principales
        self.db_manager = None
        self.main_window = None
        self.dashboard_controller = None
        self.group_controller = None
        
    def initialize(self):
        """
        Inicializa todos los componentes de la aplicación
        """
        try:
            # 1. Inicializar gestor de base de datos
            self.logger.info("Inicializando gestor de base de datos...")
            self.db_manager = DatabaseManager()
            
            # 2. Probar conexión a la base de datos
            if not self._test_database_connection():
                raise Exception("No se pudo conectar a la base de datos")
            
            # 3. Inicializar controladores
            self.logger.info("Inicializando controladores...")
            self.dashboard_controller = DashboardController(self.db_manager)
            self.group_controller = GroupController(self.db_manager)
            
            # 4. Crear ventana principal
            self.logger.info("Creando interfaz principal...")
            self.main_window = MainWindow(
                self.root,
                self.dashboard_controller,
                self.group_controller
            )
            
            # 5. Cargar datos iniciales
            self.logger.info("Cargando datos iniciales...")
            self.dashboard_controller.load_initial_data()
            self.group_controller.load_initial_data()
            
            self.logger.info("Aplicación inicializada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error durante la inicialización: {e}")
            messagebox.showerror(
                "Error de Inicialización",
                f"No se pudo inicializar la aplicación:\n\n{e}\n\nRevisa la configuración de la base de datos."
            )
            raise
    
    def _test_database_connection(self):
        """
        Prueba la conexión a la base de datos
        """
        try:
            connection = self.db_manager.get_connection()
            if connection:
                connection.close()
                self.logger.info("Conexión a la base de datos exitosa")
                return True
            else:
                self.logger.error("No se pudo establecer conexión a la base de datos")
                return False
        except Exception as e:
            self.logger.error(f"Error probando conexión a la base de datos: {e}")
            return False
    
    def cleanup(self):
        """
        Limpia recursos antes de cerrar la aplicación
        """
        try:
            self.logger.info("Iniciando limpieza de recursos...")
            
            # Cerrar conexiones de base de datos
            if self.db_manager:
                self.db_manager.close_all_connections()
            
            # Limpiar controladores
            if self.dashboard_controller:
                self.dashboard_controller.cleanup()
            
            if self.group_controller:
                self.group_controller.cleanup()
            
            self.logger.info("Limpieza de recursos completada")
            
        except Exception as e:
            self.logger.error(f"Error durante la limpieza: {e}")
    
    def handle_application_error(self, error):
        """
        Maneja errores a nivel de aplicación
        """
        self.logger.error(f"Error de aplicación: {error}")
        messagebox.showerror("Error", f"Ha ocurrido un error:\n{error}")
    
    def get_database_manager(self):
        """Getter para el gestor de base de datos"""
        return self.db_manager
    
    def get_dashboard_controller(self):
        """Getter para el controlador del dashboard"""
        return self.dashboard_controller
    
    def get_group_controller(self):
        """Getter para el controlador de grupos"""
        return self.group_controller