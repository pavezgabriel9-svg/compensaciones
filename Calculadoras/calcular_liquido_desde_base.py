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


def calcular_liquido_desde_base(sueldo_base):
    # Descuentos:
    ingreso_minimo = 529_000  # estimado Mayo 2025
    tasa_afp = 0.1049  # AFP Uno
    tasa_salud = 0.07  # Fonasa
    tasa_cesant = 0.006  # Seguro cesantía 
    movilizacion = 40_000  # Haber no imponible
    
    # Gratificación legal
    tope_gratificacion_mensual = 4.75 * ingreso_minimo / 12
    gratificacion = min(0.25 * sueldo_base, tope_gratificacion_mensual)
    
    # Total imponible
    imponible = sueldo_base + gratificacion
    
    # Descuentos previsionales y salud
    cotiz_prev = imponible * tasa_afp
    cotiz_salud = imponible * tasa_salud
    cesantia = imponible * tasa_cesant
    
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

    print("\nHaberes Imponibles:")
    print(f"Sueldo Base: ${sueldo_base:,.0f}")
    print(f"Gratificación legal: ${gratificacion:,.0f}")
    print(f"Total Imponible: ${imponible:,.0f}")
    print("Haberes no Imponibles:")
    print(f"Movilización: ${movilizacion:,.0f}")
    print(f"Total Haberes: ${total_haberes:,.0f}")
    print("\nDescuentos:")
    print(f" - AFP (10.49%): ${cotiz_prev:,.0f}")
    print(f" - Salud (7%): ${cotiz_salud:,.0f}")
    print(f" - Cesantía (0.6%): ${cesantia:,.0f}")
    print(f" - Impuesto 2ª Cat.: ${impuesto2cat:,.0f}")
    print(f"Base Tributable: ${base_tributable:,.0f}")
    print(f"Total Descuentos: ${total_descuentos:,.0f}")
    print(f"\nSueldo Líquido: ${sueldo_liquido:,.0f}")
    print(f"\n")


calcular_liquido_desde_base(1_2_000)