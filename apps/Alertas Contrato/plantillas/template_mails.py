from datetime import datetime

def _generar_html_para_jefe(self, jefe, email_jefe, alertas_jefe, modo_prueba=False):
    """Genera HTML personalizado para cada jefe"""
    modo_texto = "<div style='background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin-bottom: 20px; border-radius: 5px;'><strong>🧪 MODO PRUEBA:</strong> Este correo habría sido enviado a " + email_jefe + "</div>" if modo_prueba else ""
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }}
            h2 {{ color: #e74c3c; }}
            .jefe-header {{ background-color: #3498db; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .alerta-container {{ border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
            .alerta-header {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; margin-bottom: 10px; }}
            .urgente {{ background-color: #fce4e4; border-left: 5px solid #e74c3c; }}
            .vencida {{ background-color: #ffcdd2; border-left: 5px solid #c62828; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #34495e; color: white; }}
            .resumen {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .footer {{ background-color: #f8f9fa; padding: 15px; margin-top: 30px; border-radius: 5px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        {modo_texto}
        
        <div class="jefe-header">
            <h2>Alertas de Contratos - {jefe}</h2>
            <p>Alertas pendientes para miembros de su equipo</p>
        </div>
        
        <div class="resumen">
            <h3>Resumen</h3>
            <p><strong>Total de alertas:</strong> {len(alertas_jefe)}</p>
            <p><strong>Colaboradores afectados:</strong> {', '.join(alertas_jefe['Empleado'].tolist())}</p>
            <p><strong>Fecha de generación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>

        <p>Estimado/a <strong>{jefe}</strong>,</p>
        <p>Junto con saludar, le informamos que tiene <strong>{len(alertas_jefe)} alerta(s)</strong> de contratos pendientes de revisión en su equipo:</p>
    """

    # Agregar cada alerta del jefe
    for _, row in alertas_jefe.iterrows():
        dias_hasta = row["Días hasta alerta"]
        clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
        
        # Filtrar permisos para el empleado actual
        incidencias_empleado = self.incidencias_df[self.incidencias_df['rut_empleado'] == row['RUT']]
        
        html += f"""
        <div class="alerta-container {clase_css}">
            <div class="alerta-header">👤 {row['Empleado']} - {row['Cargo']}</div>
            <p><strong>Motivo:</strong> {row['Motivo']}</p>
            <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
            <p><strong>Días hasta la fecha:</strong> {dias_hasta} días</p>
        """
        
        # Tabla de permisos
        if not incidencias_empleado.empty:
            html += """
            <h4>📅 Permisos/Licencias Activas:</h4>
            <table>
                <thead>
                    <tr>
                        <th>Tipo de Permiso</th>
                        <th>Fecha de Inicio</th>
                        <th>Fecha de Fin</th>
                    </tr>
                </thead>
                <tbody>
            """
            for _, inc_row in incidencias_empleado.iterrows():
                html += f"""
                    <tr>
                        <td>{inc_row['tipo_permiso']}</td>
                        <td>{inc_row['fecha_inicio']}</td>
                        <td>{inc_row['fecha_fin']}</td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>Este colaborador/a no registra ausencias, permisos y/o licencias activas.</p>"
            
        html += """
        </div>
        """
    return html

def _generar_html_reporte_seleccionadas(self, alertas_seleccionadas):
    """Genera el HTML del reporte solo para las alertas seleccionadas"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h2 {{ color: #e74c3c; }}
            .alerta-container {{ border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
            .alerta-header {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; }}
            .urgente {{ background-color: #fce4e4; }}
            .vencida {{ background-color: #ffcdd2; }}
            .seleccionada {{ background-color: #e8f5e8; border-color: #27ae60; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #34495e; color: white; }}
        </style>
    </head>
    <body>

        <p>Estimado/a, junto con saludar</p>
        <p>Se adjunta el listado de colaboradores con contratos pendientes de revisión:</p>

        <div class="resumen">
            <h3>Reporte Vencimiento de Contrato</h3>
        </div>
    
    """

    # Bucle para crear una sección por cada alerta seleccionada
    for _, row in alertas_seleccionadas.iterrows():
        dias_hasta = row["Días hasta alerta"]
        clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
        clase_css += " seleccionada"  # Agregar clase para destacar que fue seleccionada
        
        # Filtrar permisos para el empleado actual
        incidencias_empleado = self.incidencias_df[self.incidencias_df['rut_empleado'] == row['RUT']]
        
        # HTML para la alerta del empleado
        html += f"""
        <div class="alerta-container {clase_css}">
            <div class="alerta-header">Termino Contrato: {row['Empleado']}</div>
            <p><strong>Cargo:</strong> {row['Cargo']}</p>
            <p><strong>Motivo:</strong> {row['Motivo']}</p>
            <p><strong>Jefe Directo:</strong> {row['Jefe']} </p>
            <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
        """
        
        # HTML para la tabla de permisos
        if not incidencias_empleado.empty:
            html += """
            <h4>Permisos Activos:</h4>
            <table>
                <thead>
                    <tr>
                        <th>Tipo de Permiso</th>
                        <th>Fecha de Inicio</th>
                        <th>Fecha de Fin</th>
                    </tr>
                </thead>
                <tbody>
            """
            for _, inc_row in incidencias_empleado.iterrows():
                html += f"""
                    <tr>
                        <td>{inc_row['tipo_permiso']}</td>
                        <td>{inc_row['fecha_inicio']}</td>
                        <td>{inc_row['fecha_fin']}</td>
                    </tr>
                """
            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>Este colaborador/a no registra ausencias, permisos y/o licencias.</p>"
            
        html += """
        </div>
        """

    html += f"""
    <br>

    <p><em><strong>Generado automáticamente por el Sistema de Alertas de Contratos de RRHH</strong></em></p>
    </body>
    </html>
    """
    return html

def _generar_html_reporte_por_jefe(nombre_jefe, empleados_data):
    """Genera HTML consolidado para un jefe específico"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Alertas de Contratos</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #007bff;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #007bff;
                margin: 0;
                font-size: 28px;
            }}
            .jefe-info {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 25px;
            }}
            .jefe-info h2 {{
                margin: 0;
                color: #1565c0;
            }}
            .summary {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #007bff;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .urgente {{
                background-color: #ffebee !important;
            }}
            .tipo-alerta {{
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            .segundo-plazo {{
                background: #fff3cd;
                color: #856404;
            }}
            .indefinido {{
                background: #f8d7da;
                color: #721c24;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #dee2e6;
                text-align: center;
                color: #6c757d;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ Alertas de Contratos</h1>
                <p>Empleados que requieren atención inmediata</p>
            </div>
            
            <div class="jefe-info">
                <h2>👤 {nombre_jefe}</h2>
                <p>Los siguientes empleados bajo su supervisión requieren atención:</p>
            </div>
            
            <div class="summary">
                <strong>📊 Resumen:</strong> {len(empleados_data)} empleado(s) requieren revisión de contrato
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>👤 Empleado</th>
                        <th>💼 Cargo</th>
                        <th>📅 Fecha Inicio</th>
                        <th>📝 Motivo</th>
                        <th>🏷️ Tipo Alerta</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for emp in empleados_data:
        clase_fila = "urgente" if emp['tipo_alerta'] == 'INDEFINIDO' else ""
        clase_tipo = "indefinido" if emp['tipo_alerta'] == 'INDEFINIDO' else "segundo-plazo"
        
        html += f"""
                    <tr class="{clase_fila}">
                        <td><strong>{emp['empleado']}</strong></td>
                        <td>{emp['cargo']}</td>
                        <td>{emp['fecha_inicio']}</td>
                        <td>{emp['motivo']}</td>
                        <td><span class="tipo-alerta {clase_tipo}">{emp['tipo_alerta']}</span></td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
            
            <div class="footer">
                <p><strong>⏰ Acción requerida:</strong> Por favor revise y tome las acciones necesarias para estos contratos.</p>
                <p>📧 Este es un correo automático generado por el Sistema de Alertas de Contratos</p>
                <hr>
                <small>Para consultas, contacte al área de Recursos Humanos</small>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html
