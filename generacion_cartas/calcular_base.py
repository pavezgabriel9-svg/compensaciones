def impuesto_unico(imponible):
    '''
    Tramos SII agosto 2025 (pesos mensuales)
    '''
    tramos = [
        #desde, hasta, factor, rebaja
        (0, 926_734.50, 0.0, 0.0),
        (926_734.51, 2_059_410.00, 0.04, 37_069.38),
        (2_059_410.01, 3_432_350.00, 0.08, 119_445.78),
        (3_432_350.01, 4_805_290.00, 0.135, 308_225.03),
        (4_805_290.01, 6_178_230.00, 0.23, 764_727.58),
        (6_178_230.01, 8_237_640.00, 0.304, 1_221_916.60),
        (8_237_640.01, 21_280_570.00, 0.35, 1_600_848.04),
        (21_280_570.01, float('inf'), 0.40, 2_664_876.54),
    ]
    
    for desde, hasta, factor, rebaja in tramos:
        if desde <= imponible <= hasta:
            impuesto = imponible * factor - rebaja
            return max(impuesto, 0.0)
    return 0.0


def calcular_sueldo_base(sueldo_liquido_deseado, precision=100, tipo_salud="isapre"):
    ''''
    Calcula el sueldo base necesario para alcanzar un sueldo líquido deseado. 
    La precisión es expresada en pesos.
    tipo_salud: "fonasa" o "isapre"
    '''
    
    #----------------------------------------------------------
                # Parámetros - mantener actualizado
    #----------------------------------------------------------
    ingreso_minimo = 529_000
    uf = 39_247
    max_imponible_afp_salud = 87.8   # Tope imponible AFP y salud
    max_imponible_seguro_cesantia = 131.8  # Tope imponible Seguro Cesantía
    
    # Tasas y topes
    tasa_afp = 0.1049  # AFP Uno
    tasa_fonasa = 0.07  # Fonasa (porcentaje)
    valor_isapre_uf = 4.78  # Isapre (valor fijo en UF)
    tasa_cesantia_trabajador = 0.006 # Seguro de Cesantía (trabajador)
    
    # Seleccionar tipo de salud
    if tipo_salud.lower() == "isapre":
        nombre_salud = "Isapre"
        cotizacion_salud_fija = valor_isapre_uf * uf  # Valor fijo en pesos
    else:
        nombre_salud = "Fonasa"
        cotizacion_salud_fija = None  # Se calcula como porcentaje

    # Movilización
    movilizacion = 40_000  # Haber no imponible, fijo Cramer
    
    # Conversión tope imponible (UF) a pesos
    tope_imponible_pesos_afp_salud = max_imponible_afp_salud * uf
    tope_imponible_seguro_cesantia_pesos = max_imponible_seguro_cesantia * uf

    # Función para estimar el líquido desde un sueldo base
    def estimar_liquido(sueldo_base):
        tope_gratificacion_mensual = 4.75 * ingreso_minimo / 12
        gratificacion = min(0.25 * sueldo_base, tope_gratificacion_mensual)

        imponible = sueldo_base + gratificacion

        cotiz_prev = min(imponible * tasa_afp, tope_imponible_pesos_afp_salud)
        
        # Calcular cotización de salud según tipo
        if cotizacion_salud_fija is not None:  # Isapre
            cotiz_salud = cotizacion_salud_fija
        else:  # Fonasa
            cotiz_salud = min(imponible * tasa_fonasa, tope_imponible_pesos_afp_salud)
            
        cesantia = min(imponible * tasa_cesantia_trabajador, tope_imponible_seguro_cesantia_pesos)

        base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
        impuesto2cat = impuesto_unico(base_tributable)

        total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
        total_haberes = imponible + movilizacion
        return total_haberes - total_descuentos

    # Rango inicial dinámico
    sueldo_min = 0
    sueldo_max = sueldo_liquido_deseado
    while estimar_liquido(sueldo_max) < sueldo_liquido_deseado:
        sueldo_max *= 2 # Duplicar hasta encontrar un rango que contenga el sueldo deseado
    
    # Búsqueda binaria
    while sueldo_max - sueldo_min > precision:
        sueldo_base = (sueldo_min + sueldo_max) / 2
        sueldo_liquido_calculado = estimar_liquido(sueldo_base)
        
        if sueldo_liquido_calculado < sueldo_liquido_deseado:
            sueldo_min = sueldo_base
        else:
            sueldo_max = sueldo_base
    
    sueldo_base = round(sueldo_base)
    
    # Recalculamos todo con el sueldo base encontrado
    tope_grat_mensual = 4.75 * ingreso_minimo / 12
    gratificacion = min(0.25 * sueldo_base, tope_grat_mensual)
    imponible = sueldo_base + gratificacion
    cotiz_prev = min(imponible * tasa_afp, tope_imponible_pesos_afp_salud)
    
    # Calcular cotización de salud según tipo
    if cotizacion_salud_fija is not None:  # Isapre
        cotiz_salud = cotizacion_salud_fija
        texto_salud = f" - {nombre_salud} ({valor_isapre_uf}UF): ${cotiz_salud:,.0f}"
    else:  # Fonasa
        cotiz_salud = min(imponible * tasa_fonasa, tope_imponible_pesos_afp_salud)
        texto_salud = f" - {nombre_salud} ({tasa_fonasa*100:.1f}%): ${cotiz_salud:,.0f}"
    
    cesantia = min(imponible * tasa_cesantia_trabajador, tope_imponible_seguro_cesantia_pesos)
    #cesantia_empleador = min(imponible * tasa_cesant_empleador, tope_imponible_sc_pesos)
    base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
    impuesto2cat = impuesto_unico(base_tributable)
    total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
    total_haberes = imponible + movilizacion
    sueldo_liquido = total_haberes - total_descuentos
    #costo_empleador = imponible + cesantia_empleador #sis_empleador
    
    # Salida
    print(f"\n\n")
    print(f"CÁLCULO DE SUELDO BASE")
    print(f"\nOBJETIVO: Sueldo líquido de ${sueldo_liquido_deseado:,.0f}")
    print(f"RESULTADO: Sueldo base necesario ${sueldo_base:,.0f}")
    
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
    
    print(f"\n--- RESULTADO TRABAJADOR ---")
    print(f"Base Tributable: ${base_tributable:,.0f}")
    print(f"SUELDO LÍQUIDO: ${sueldo_liquido:,.0f}")
    print(f"Diferencia con objetivo: ${sueldo_liquido - sueldo_liquido_deseado:,.0f}")
    
    # print(f"\n--- COSTOS EMPLEADOR ---")
    # print(f"Imponible: ${imponible:,.0f}")
    # print(f"SIS ({tasa_sis*100:.2f}%): ${sis_empleador:,.0f}")
    # print(f"Seguro Cesantía empleador ({tasa_cesant_empleador*100:.1f}%): ${cesantia_empleador:,.0f}")
    # print(f"COSTO TOTAL EMPLEADOR: ${costo_empleador:,.0f}")

    #información técnica
    print(f"\n--- INFORMACIÓN TÉCNICA ---")
    print(f"Valor UF utilizado: ${uf:,.3f}")
    # print(f"Tope AFP/Salud: {max_imponible_afp_salud}UF = ${tope_imponible_pesos_afp_salud:,.0f}")
    # print(f"Tope Cesantía: {max_imponible_seguro_cesantia}UF = ${tope_imponible_seguro_cesantia_pesos:,.0f}")
    if imponible > tope_imponible_pesos_afp_salud:
        print(f"Se alcanzó el tope imponible AFP/Salud")
    if imponible > tope_imponible_seguro_cesantia_pesos:
        print(f"Se alcanzó el tope imponible Cesantía")
    print(f"\n\n")
    return sueldo_base

calcular_sueldo_base(1_000_000, tipo_salud="fonasa")












#rescatar funcionalidad para agregar haberes extras

# def impuesto_unico(imponible):
#     '''
#     Tramos SII agosto 2025 (pesos mensuales)
#     '''
#     tramos = [
#         (0, 926_734.50, 0.0, 0.0),
#         (926_734.51, 2_059_410.00, 0.04, 37_069.38),
#         (2_059_410.01, 3_432_350.00, 0.08, 119_445.78),
#         (3_432_350.01, 4_805_290.00, 0.135, 308_225.03),
#         (4_805_290.01, 6_178_230.00, 0.23, 764_727.58),
#         (6_178_230.01, 8_237_640.00, 0.304, 1_221_916.60),
#         (8_237_640.01, 21_280_570.00, 0.35, 1_600_848.04),
#         (21_280_570.01, float('inf'), 0.40, 2_664_876.54),
#     ]
    
#     for lower, upper, factor, rebate in tramos:
#         if lower <= imponible <= upper:
#             impuesto = imponible * factor - rebate
#             return max(impuesto, 0.0)
#     return 0.0

# def calcular_sueldo_base_desde_liquido(sueldo_liquido_deseado, haberes_extras=0, precision=100):
#     # Obtener valor UF actualizado
#     #valor_uf = obtener_valor_uf()
#     valor_uf = 39179
#     tope_imponible = 87.8 * valor_uf

#     # Parámetros
#     ingreso_minimo =  529_000  #2025
#     tasa_afp = 0.1049  # AFP Uno
#     tasa_salud = 0.07  # Fonasa
#     tasa_cesantia = 0.006  # Seguro Cesantía Indefinido
#     movilizacion = 40_000  # Haber no imponible
     

#     sueldo_min = 0
#     sueldo_max = sueldo_liquido_deseado * 3
    
#     while sueldo_max - sueldo_min > precision:
#         sueldo_base = (sueldo_min + sueldo_max) / 2
#         tope_grat_mensual = 4.75 * ingreso_minimo / 12
#         gratificacion = min(0.25 * sueldo_base, tope_grat_mensual)
        
#         imponible = sueldo_base + gratificacion + haberes_extras
#         imponible_afecto = min(imponible, tope_imponible)

#         cotiz_prev = imponible_afecto * tasa_afp
#         cotiz_salud = imponible_afecto * tasa_salud
#         cesantia = imponible_afecto * tasa_cesantia
        
#         base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
#         impuesto2cat = impuesto_unico(base_tributable)
        
#         total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
#         total_haberes = imponible + movilizacion
#         sueldo_liquido_calculado = total_haberes - total_descuentos
        
#         if sueldo_liquido_calculado < sueldo_liquido_deseado:
#             sueldo_min = sueldo_base
#         else:
#             sueldo_max = sueldo_base

#     sueldo_base = round(sueldo_base)

#     # Cálculo final con sueldo_base encontrado
#     tope_grat_mensual = 4.75 * ingreso_minimo / 12
#     gratificacion = min(0.25 * sueldo_base, tope_grat_mensual)
#     imponible = sueldo_base + gratificacion + haberes_extras
#     imponible_afecto = min(imponible, tope_imponible)

#     cotiz_prev = imponible_afecto * tasa_afp
#     cotiz_salud = imponible_afecto * tasa_salud
#     cesantia = imponible_afecto * tasa_cesantia
#     base_tributable = imponible - (cotiz_prev + cotiz_salud + cesantia)
#     impuesto2cat = impuesto_unico(base_tributable)
#     total_descuentos = cotiz_prev + cotiz_salud + cesantia + impuesto2cat
#     total_haberes = imponible + movilizacion
#     sueldo_liquido = total_haberes - total_descuentos

#     print(f"\nValor UF actualizado: ${valor_uf:,.2f}")
#     print(f"Tope imponible legal (87,8 UF): ${tope_imponible:,.0f}")
#     print(f"\nPara un sueldo líquido de: ${sueldo_liquido_deseado:,.0f}")
#     print(f"Se necesita un sueldo base de: ${sueldo_base:,.0f}")
#     print(f'\nHaberes:')
#     print(f'Sueldo base: ${sueldo_base:,.0f}')
#     print(f"Gratificación legal: ${gratificacion:,.0f}")
#     print(f"Haberes imponibles extras: ${haberes_extras:,.0f}")
#     print(f"Total Imponible: ${imponible:,.0f}")
#     print(f"Haberes no imponibles: ${movilizacion:,.0f}")
#     print("\nDescuentos:")
#     print(f" - AFP (10.49%): ${cotiz_prev:,.0f}")
#     print(f" - Salud (7%): ${cotiz_salud:,.0f}")
#     print(f" - Cesantía (0.6%): ${cesantia:,.0f}")
#     print(f" - Impuesto 2ª Cat.: ${impuesto2cat:,.0f}")
#     print(f"Base Tributable: ${base_tributable:,.0f}")
#     print(f"Total Descuentos: ${total_descuentos:,.0f}")
#     print(f"\nDiferencia con el deseado: ${sueldo_liquido - sueldo_liquido_deseado:,.0f}\n")
    
#     return sueldo_base

# # Ejecutar simulación
# calcular_sueldo_base_desde_liquido(1_250_000, haberes_extras=100_000)