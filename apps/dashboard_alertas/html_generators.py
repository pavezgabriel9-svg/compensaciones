from datetime import datetime

def generar_html_para_jefe(jefe, email_jefe, alertas_jefe, incidencias_df, mail_test_gabriel, modo_prueba=False):
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
            <h2>📋 Alertas de Contratos - {jefe}</h2>
            <p>Alertas pendientes para miembros de su equipo</p>
        </div>
        
        <div class="resumen">
            <h3>📊 Resumen</h3>
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
        incidencias_empleado = incidencias_df[incidencias_df['rut_empleado'] == row['RUT']]
        
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
            html += "<p>✅ Este colaborador/a no registra ausencias, permisos y/o licencias activas.</p>"
            
        html += """
        </div>
        """

    html += f"""
        <div class="footer">
            <h4>📞 ¿Necesita ayuda?</h4>
            <p>Si tiene consultas sobre estas alertas o necesita apoyo para la renovación de contratos, 
            no dude en contactar al área de Recursos Humanos.</p>
            
            <p><strong>Equipo de Recursos Humanos</strong><br>
            📧 Email: {mail_test_gabriel}<br>
            📅 Sistema de Alertas de Contratos</p>
            
            <hr style="margin: 20px 0;">
            <p style="font-size: 0.8em; color: #666;">
                <em>Este correo fue generado automáticamente por el Sistema de Alertas de Contratos de RRHH. 
                Para consultas técnicas, contacte al administrador del sistema.</em>
            </p>
        </div>
    </body>
    </html>
    """
    return html


def generar_html_reporte_seleccionadas(alertas_seleccionadas, incidencias_df):
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
            .resumen {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="resumen">
            <h3>Reporte Vencimiento de Contrato</h3>
        </div>
        
        <p>Estimado/a, junto con saludar</p>
        <p>Se adjunta el listado de colaboradores con contratos pendientes de revisión:</p>
    """

    # Bucle para crear una sección por cada alerta seleccionada
    for _, row in alertas_seleccionadas.iterrows():
        dias_hasta = row["Días hasta alerta"]
        clase_css = "vencida" if dias_hasta <= 0 else "urgente" if row["Urgente"] == 1 else ""
        clase_css += " seleccionada"
        
        # Filtrar permisos para el empleado actual
        incidencias_empleado = incidencias_df[incidencias_df['rut_empleado'] == row['RUT']]
        
        html += f"""
        <div class="alerta-container {clase_css}">
            <div class="alerta-header">✅ Termino Contrato: {row['Empleado']}</div>
            <p><strong>Cargo:</strong> {row['Cargo']}</p>
            <p><strong>Motivo:</strong> {row['Motivo']}</p>
            <p><strong>Jefe Directo:</strong> {row['Jefe']} </p>
            <p><strong>Fecha de Renovación:</strong> {row['Fecha alerta']}</p>
        """
        
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
    <div class="resumen">
        <p><strong>Resumen del envío:</strong></p>
        <ul>
            <li>Alertas seleccionadas: {len(alertas_seleccionadas)}</li>
            <li>Empleados: {', '.join(alertas_seleccionadas['Empleado'].tolist())}</li>
        </ul>
    </div>
    <p><em><strong>Generado automáticamente por el Sistema de Alertas de Contratos de RRHH</strong></em></p>
    </body>
    </html>
    """
    return html
