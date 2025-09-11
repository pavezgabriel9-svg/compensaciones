def impuesto_unico(imponible):
    '''
    Tramos SII agosto 2025 (pesos mensuales)
    '''
    tramos = [
        (0, 926_734.50, 0.0, 0.0),
        (926_734.51, 2_059_410.00, 0.04, 37_069.38),
        (2_059_410.01, 3_432_350.00, 0.08, 119_445.78),
        (3_432_350.01, 4_805_290.00, 0.135, 308_225.03),
        (4_805_290.01, 6_178_230.00, 0.23, 764_727.58),
        (6_178_230.01, 8_237_640.00, 0.304, 1_221_916.60),
        (8_237_640.01, 21_280_570.00, 0.35, 1_600_848.04),
        (21_280_570.01, float('inf'), 0.40, 2_664_876.54),
    ]
    
    for lower, upper, factor, rebate in tramos:
        if lower <= imponible <= upper:
            impuesto = imponible * factor - rebate
            return max(impuesto, 0.0)
    
    return 0.0


def calcular_liquido_desde_base(sueldo_base, tipo_salud="fonasa", valor_isapre_uf=None, verbose=True):
    '''
    Calcula el sueldo líquido a partir del sueldo base.
    tipo_salud: "fonasa" o "isapre"
    valor_isapre_uf: Valor en UF de la Isapre (solo si tipo_salud es "isapre")
    '''
    # Parámetros - agosto 2025
    ingreso_minimo = 529_000
    uf = 39_486
    max_imponible_afp_salud = 87.8   # Tope imponible AFP y salud
    max_imponible_seguro_cesantia = 131.8  # Tope imponible Seguro Cesantía
    
    # Tasas y topes
    tasa_afp = 0.1049  # AFP Uno
    tasa_fonasa = 0.07  # Fonasa (porcentaje)
    tasa_cesantia_trabajador = 0.006  # Seguro de Cesantía (trabajador)
    tasa_cesantia_empleador = 0.024  # Seguro de Cesantía (empleador, contrato indefinido)
    tasa_sis = 0.016  # Seguro de Invalidez y Sobrevivencia (empleador)
    
    # Verificación básica para evitar errores comunes
    if sueldo_base < 500_000:
        print(f"\n⚠️ ADVERTENCIA: Sueldo base de ${sueldo_base:,.0f} parece muy bajo.")
        print(f"Un sueldo base típico está en cientos de miles o millones de pesos.")
    
    # Movilización
    movilizacion = 40_000  # Haber no imponible
    
    # Seleccionar tipo de salud
    if tipo_salud.lower() == "isapre":
        nombre_salud = "Isapre"
        # Si no se especifica, usamos un valor por defecto
        if not valor_isapre_uf:
            valor_isapre_uf = 4.78
        cotizacion_salud_fija = valor_isapre_uf * uf  # Valor fijo en pesos
    else:
        nombre_salud = "Fonasa"
        cotizacion_salud_fija = None  # Se calcula como porcentaje
    
    # Conversión tope imponible (UF) a pesos
    tope_imponible_pesos_afp_salud = max_imponible_afp_salud * uf
    tope_imponible_seguro_cesantia_pesos = max_imponible_seguro_cesantia * uf
    
    # Gratificación legal
    tope_gratificacion_mensual = 4.75 * ingreso_minimo / 12
    gratificacion = min(0.25 * sueldo_base, tope_gratificacion_mensual)
    
    # Total imponible
    imponible = sueldo_base + gratificacion
    
    # Descuentos previsionales y salud con topes
    cotiz_prev = min(imponible * tasa_afp, tope_imponible_pesos_afp_salud * tasa_afp)
    
    # Calcular cotización de salud según tipo
    if cotizacion_salud_fija is not None:  # Isapre
        cotiz_salud = cotizacion_salud_fija
        texto_salud = f" - {nombre_salud} ({valor_isapre_uf}UF): ${cotiz_salud:,.0f}"
    else:  # Fonasa
        cotiz_salud = min(imponible * tasa_fonasa, tope_imponible_pesos_afp_salud * tasa_fonasa)
        texto_salud = f" - {nombre_salud} ({tasa_fonasa*100:.1f}%): ${cotiz_salud:,.0f}"
    
    cesantia = min(imponible * tasa_cesantia_trabajador, tope_imponible_seguro_cesantia_pesos * tasa_cesantia_trabajador)
    
    # Base tributable
    base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
    
    # Impuesto único con tramos reales
    impuesto2cat = impuesto_unico(base_tributable)
    
    # Suma descuentos
    total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
    
    # Total haberes
    total_haberes = imponible + movilizacion
    
    # Líquido final
    sueldo_liquido = total_haberes - total_descuentos

    # Costos del empleador
    cesantia_empleador = min(imponible * tasa_cesantia_empleador, tope_imponible_seguro_cesantia_pesos * tasa_cesantia_empleador)
    sis_empleador = min(imponible * tasa_sis, tope_imponible_pesos_afp_salud * tasa_sis)
    costo_empleador = imponible + cesantia_empleador + sis_empleador

    # Solo imprimir si verbose=True
    if verbose:
        print(f"\n\n")
        print(f"CÁLCULO DE SUELDO LÍQUIDO")
        print(f"\nSueldo base de ${sueldo_base:,.0f}")
        print(f"Sueldo Líquido: ${sueldo_liquido:,.0f}")
        
        print(f'\n--- HABERES ---')
        print(f'Sueldo base: ${sueldo_base:,.0f}')
        print(f"Gratificación legal: ${gratificacion:,.0f}")
        print(f"Total Imponible: ${imponible:,.0f}")
        print(f"Haberes no imponibles: ${movilizacion:,.0f}")
        print(f"TOTAL HABERES: ${total_haberes:,.0f}")
        
        print(f"\n--- DESCUENTOS TRABAJADOR ---")
        print(f" - AFP ({tasa_afp*100:.2f}%): ${cotiz_prev:,.0f}")
        print(texto_salud)
        print(f" - Seguro Cesantía ({tasa_cesantia_trabajador*100:.1f}%): ${cesantia:,.0f}")
        print(f" - Impuesto 2ª Cat.: ${impuesto2cat:,.0f}")
        print(f"TOTAL DESCUENTOS: ${total_descuentos:,.0f}")
        
        # print(f"\n--- RESULTADO TRABAJADOR ---")
        # print(f"Base Tributable: ${base_tributable:,.0f}")
        # print(f"SUELDO LÍQUIDO: ${sueldo_liquido:,.0f}")
        
        # print(f"\n--- COSTOS EMPLEADOR ---")
        # print(f"Imponible: ${imponible:,.0f}")
        # print(f"SIS ({tasa_sis*100:.2f}%): ${sis_empleador:,.0f}")
        # print(f"Seguro Cesantía empleador ({tasa_cesantia_empleador*100:.1f}%): ${cesantia_empleador:,.0f}")
        # print(f"COSTO TOTAL EMPLEADOR: ${costo_empleador:,.0f}")

        # Información técnica
        print(f"\n--- INFORMACIÓN TÉCNICA ---")
        print(f"Valor UF utilizado: ${uf:,.3f}")
        #print(f"Tope AFP/Salud: {max_imponible_afp_salud}UF = ${tope_imponible_pesos_afp_salud:,.0f}")
        #print(f"Tope Cesantía: {max_imponible_seguro_cesantia}UF = ${tope_imponible_seguro_cesantia_pesos:,.0f}")
        if imponible > tope_imponible_pesos_afp_salud:
            print(f"Se alcanzó el tope imponible AFP/Salud")
        if imponible > tope_imponible_seguro_cesantia_pesos:
            print(f"Se alcanzó el tope imponible Cesantía")
        print(f"\n\n")
    
    return sueldo_liquido

# Uso
if __name__ == "__main__":
    # Ejemplo con Fonasa
    #print("EJEMPLO CON FONASA:")
    calcular_liquido_desde_base(922_000, "fonasa")

    # Ejemplo con Isapre
    # print("EJEMPLO CON ISAPRE:")
    # calcular_liquido_desde_base(1_200_000, "isapre", 3.5)