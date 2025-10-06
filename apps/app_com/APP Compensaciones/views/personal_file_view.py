
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from controllers import personal_file_controller

class PersonalFileView(tk.Toplevel):
    def __init__(self, parent, rut, data_df, employees_df, settlements_df):
        super().__init__(parent)
        self.rut = rut
        
        self.df_persona, self.emp_info = personal_file_controller.preparar_datos_ficha(
            rut, data_df, employees_df, settlements_df
        )

        if self.df_persona is None:
            messagebox.showerror("Error", f"No se pudieron cargar los datos para el RUT: {rut}")
            self.destroy()
            return

        self._configurar_ventana()
        self._crear_widgets()
        
        print(self.df_persona.columns)
        print(self.emp_info.columns)
        
    def _configurar_ventana(self):
        nombre_persona = self.df_persona['full_name'].iloc[0]
        self.title(f"Ficha de {nombre_persona}")
        self.geometry("1200x800+100+50")
        self.configure(bg='#f8f9fa')
        self.grab_release()
        self.focus()

    def _crear_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña Datos Generales
        frame_datos = ttk.Frame(notebook)
        notebook.add(frame_datos, text="General")
        self._crear_pestaña_datos_generales(frame_datos)

        # Pestaña Historial posiciones
        frame_historial = ttk.Frame(notebook)
        notebook.add(frame_historial, text="Evolución")
        self._crear_pestaña_evolucion(frame_historial)
        
        # Pestaña Historial liquidaciones
        frame_historial = ttk.Frame(notebook)
        notebook.add(frame_historial, text="Histórico Liquidaciones")
        self._crear_pestaña_liquidaciones(frame_historial)

    def _crear_pestaña_datos_generales(self, parent_frame):
        canvas = tk.Canvas(parent_frame, bg='#f8f9fa', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        self._crear_tarjetas_info(scrollable_frame)
        self._crear_grafico_evolucion(scrollable_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
         
        
    def _crear_tarjetas_info(self, parent):
        ultimo_registro = self.df_persona.iloc[-1]
        
        header = tk.Frame(parent, bg='#f8f9fa')
        header.pack(fill='x', pady=(5, 0))
        tk.Label(header, text=ultimo_registro.get('full_name', 'N/A'), font=('Arial', 16, 'bold'), bg='#f8f9fa', fg='#2c3e50').pack(anchor='w', padx=8)

        cards_frame = tk.Frame(parent, bg='#f8f9fa')
        cards_frame.pack(fill='x', padx=8)

        # Función auxiliar para crear tarjetas
        def crear_card(title, data_rows):
            card = tk.LabelFrame(cards_frame, text=title, font=('Arial', 11, 'bold'), bg='white', fg='#2c3e50', padx=12, pady=10, labelanchor='n')
            card.pack(side='left', fill='both', expand=True, padx=6, pady=6)
            for i, (label, value) in enumerate(data_rows):
                tk.Label(card, text=f"{label}:", font=('Arial', 10, 'bold'), bg='white', fg='#34495e').grid(row=i, column=0, sticky='w', pady=3, padx=(0, 8))
                tk.Label(card, text=str(value), font=('Arial', 10), bg='white', fg='#2c3e50').grid(row=i, column=1, sticky='w', pady=3)

        # Datos para las tarjetas
        info_personal = [
            ("RUT", ultimo_registro.get('rut', 'N/A')),
            ("Email", self.emp_info.get('email', 'N/A') if self.emp_info is not None else 'N/A'),
            ("Estudios", self.emp_info.get('degree', 'N/A') if self.emp_info is not None else 'N/A'),
            ("Universidad", self.emp_info.get('university', 'N/A') if self.emp_info is not None else 'N/A'),
            ("Nacimiento", self.emp_info.get('birthday', 'N/A'))
        ]
        
        sueldo_base_txt = f"${ultimo_registro.get('base_wage', 0):,.0f}"
        
        info_laboral = [
            ("Cargo", ultimo_registro.get('role_name', 'N/A')),
            ("Área", ultimo_registro.get('area_name', 'N/A')),
            ("Jefatura", ultimo_registro.get('boss_name', 'N/A')),
            ("Años Servicio", f"{ultimo_registro.get('service_years', 0):.1f}"),
            ("Sueldo Base", sueldo_base_txt)
            
        ]
        
        crear_card("Información Personal", info_personal)
        crear_card("Información Laboral", info_laboral)

    def _crear_grafico_evolucion(self, parent):
        chart_frame = tk.LabelFrame(parent, text="Evolución Salarial", font=('Arial', 11, 'bold'), bg='white', fg='#2c3e50', padx=10, pady=10, labelanchor='n')
        chart_frame.pack(fill='both', expand=True, padx=8, pady=(6, 10))

        fig, ax = plt.subplots(figsize=(10, 4.8))
        
        ax.plot(self.df_persona["Fecha"], self.df_persona["base_wage"], marker='o', linewidth=2, label="Sueldo Base")
        
        if "Liquido_a_Pagar" in self.df_persona.columns and not self.df_persona["Liquido_a_Pagar"].isna().all():
            ax.plot(self.df_persona["Fecha"], self.df_persona["Liquido_a_Pagar"], marker='s', linewidth=2, label="Sueldo Líquido")

        ax.legend(fontsize=9)
        ax.set_xlabel("Período", fontsize=10)
        ax.set_ylabel("Sueldo ($)", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _crear_pestaña_evolucion(self, parent_frame):
        tk.Label(parent_frame, text=f"Evolución - {self.df_persona['full_name'].iloc[0]}", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        cols = ("Período", "Cargo", "Sueldo Base")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120)

        df_sorted = self.df_persona.sort_values("start_date", ascending=False)
        for _, row in df_sorted.iterrows():
            periodo = row['start_date'].strftime('%Y-%m')
            sueldo_base = f"${row['base_wage']:,.0f}" if pd.notna(row.get('base_wage')) else "N/A"
            tree.insert("", "end", values=(
                periodo,
                row.get("role_name", "N/A"),
                sueldo_base,
            ))
            
        tree.pack(fill='both', expand=True)
        
    def _crear_pestaña_liquidaciones(self, parent_frame):
        tk.Label(parent_frame, text=f"Historial Completo - {self.df_persona['full_name'].iloc[0]}", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree_frame = ttk.Frame(parent_frame)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        cols = ("Período", "Cargo", "Área", "Sueldo Base", "Sueldo Líquido")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=120)

        df_sorted = self.df_persona.sort_values("Fecha", ascending=False)
        for _, row in df_sorted.iterrows():
            periodo = row['Fecha'].strftime('%Y-%m')
            sueldo_base = f"${row['base_wage']:,.0f}" if pd.notna(row.get('base_wage')) else "N/A"
            sueldo_liquido = f"${row['Liquido_a_Pagar']:,.0f}" if pd.notna(row.get('Liquido_a_Pagar')) else "N/A"
            tree.insert("", "end", values=(
                periodo,
                row.get("role_name", "N/A"),
                row.get("area_name", "N/A"),
                sueldo_base,
                sueldo_liquido
            ))
            
        tree.pack(fill='both', expand=True)