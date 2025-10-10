SELECT
    a.first_level_name AS empresa,
    a.second_level_name AS división,
    a.name AS área,
    e.rut,
    e.full_name AS nombre_completo,
    e.gender AS genero,
    e.birthday AS nacimiento,
    e.active_since AS ingreso,
    e.degree AS formación, 
    pl.level AS nivel,
    e.name_role AS cargo,
    jefe.name_role AS cargo_jefe,
    jefe.full_name AS nombre_jefe,
    e.base_wage AS sueldo_base,

    -- ####################### INICIO DE BONOS ESPECÍFICOS #######################
    MAX(CASE WHEN hsi.name = 'Bono antigüedad' THEN hsi.amount ELSE 0 END) AS "Bono antigüedad",
    MAX(CASE WHEN hsi.name = 'Bono Asistencia' THEN hsi.amount ELSE 0 END) AS "Bono Asistencia",
    MAX(CASE WHEN hsi.name = 'Bono Auditores Internos' THEN hsi.amount ELSE 0 END) AS "Bono Auditores Internos",
    MAX(CASE WHEN hsi.name = 'Bono Chofer' THEN hsi.amount ELSE 0 END) AS "Bono Chofer",
    MAX(CASE WHEN hsi.name = 'Bono Colorante' THEN hsi.amount ELSE 0 END) AS "Bono Colorante",
    MAX(CASE WHEN hsi.name = 'Bono Cumplimiento meta mensual' THEN hsi.amount ELSE 0 END) AS "Bono Cumplimiento meta mensual",
    MAX(CASE WHEN hsi.name = 'Bono de Antiguedad' THEN hsi.amount ELSE 0 END) AS "Bono de Antiguedad",
    MAX(CASE WHEN hsi.name = 'Bono De Asistencia' THEN hsi.amount ELSE 0 END) AS "Bono De Asistencia",
    MAX(CASE WHEN hsi.name = 'Bono de Escolaridad' THEN hsi.amount ELSE 0 END) AS "Bono de Escolaridad",
    MAX(CASE WHEN hsi.name = 'BONO DE PERMANENCIA' THEN hsi.amount ELSE 0 END) AS "BONO DE PERMANENCIA",
    MAX(CASE WHEN hsi.name = 'BONO DE PRODUCCION' THEN hsi.amount ELSE 0 END) AS "BONO DE PRODUCCION",
    MAX(CASE WHEN hsi.name = 'Bono Emergencia' THEN hsi.amount ELSE 0 END) AS "Bono Emergencia",
    MAX(CASE WHEN hsi.name = 'Bono Empresa' THEN hsi.amount ELSE 0 END) AS "Bono Empresa",
    MAX(CASE WHEN hsi.name = 'Bono escolaridad' THEN hsi.amount ELSE 0 END) AS "Bono escolaridad",
    MAX(CASE WHEN hsi.name = 'Bono Especial' THEN hsi.amount ELSE 0 END) AS "Bono Especial",
    MAX(CASE WHEN hsi.name = 'Bono Especial Liderazgo' THEN hsi.amount ELSE 0 END) AS "Bono Especial Liderazgo",
    MAX(CASE WHEN hsi.name = 'Bono Especial Liquido' THEN hsi.amount ELSE 0 END) AS "Bono Especial Liquido",
    MAX(CASE WHEN hsi.name = 'Bono Especial Mensual' THEN hsi.amount ELSE 0 END) AS "Bono Especial Mensual",
    MAX(CASE WHEN hsi.name = 'Bono Extraordinario' THEN hsi.amount ELSE 0 END) AS "Bono Extraordinario",
    MAX(CASE WHEN hsi.name = 'Bono Fiestas Patrias' THEN hsi.amount ELSE 0 END) AS "Bono Fiestas Patrias",
    MAX(CASE WHEN hsi.name = 'Bono Gestion' THEN hsi.amount ELSE 0 END) AS "Bono Gestion",
    MAX(CASE WHEN hsi.name = 'BONO GRUPO ELECTROGENO' THEN hsi.amount ELSE 0 END) AS "BONO GRUPO ELECTROGENO",
    MAX(CASE WHEN hsi.name = 'BONO IMD' THEN hsi.amount ELSE 0 END) AS "BONO IMD",
    MAX(CASE WHEN hsi.name = 'Bono Insp Contratista' THEN hsi.amount ELSE 0 END) AS "Bono Insp Contratista",
    MAX(CASE WHEN hsi.name = 'Bono Insp. Contratista' THEN hsi.amount ELSE 0 END) AS "Bono Insp. Contratista",
    MAX(CASE WHEN hsi.name = 'Bono Jefe Area Contingencia' THEN hsi.amount ELSE 0 END) AS "Bono Jefe Area Contingencia",
    MAX(CASE WHEN hsi.name = 'Bono Jefe Unidad' THEN hsi.amount ELSE 0 END) AS "Bono Jefe Unidad",
    MAX(CASE WHEN hsi.name = 'Bono Jefes' THEN hsi.amount ELSE 0 END) AS "Bono Jefes",
    MAX(CASE WHEN hsi.name = 'Bono Jornada Extraordinaria' THEN hsi.amount ELSE 0 END) AS "Bono Jornada Extraordinaria",
    MAX(CASE WHEN hsi.name = 'BONO MATRIMONIO' THEN hsi.amount ELSE 0 END) AS "BONO MATRIMONIO",
    MAX(CASE WHEN hsi.name = 'Bono Nacimiento' THEN hsi.amount ELSE 0 END) AS "Bono Nacimiento",
    MAX(CASE WHEN hsi.name = 'Bono Navidad' THEN hsi.amount ELSE 0 END) AS "Bono Navidad",
    MAX(CASE WHEN hsi.name = 'Bono Nocturno' THEN hsi.amount ELSE 0 END) AS "Bono Nocturno",
    MAX(CASE WHEN hsi.name = 'BONO OPERARIO MASTER' THEN hsi.amount ELSE 0 END) AS "BONO OPERARIO MASTER",
    MAX(CASE WHEN hsi.name = 'Bono por fallecimiento' THEN hsi.amount ELSE 0 END) AS "Bono por fallecimiento",
    MAX(CASE WHEN hsi.name = 'Bono Responsabilidad Internaci' THEN hsi.amount ELSE 0 END) AS "Bono Responsabilidad Internaci",
    MAX(CASE WHEN hsi.name = 'Bono Resultado' THEN hsi.amount ELSE 0 END) AS "Bono Resultado",
    MAX(CASE WHEN hsi.name = 'Bono Sábado Malloco' THEN hsi.amount ELSE 0 END) AS "Bono Sábado Malloco",
    MAX(CASE WHEN hsi.name = 'Bono Secadores Spray' THEN hsi.amount ELSE 0 END) AS "Bono Secadores Spray",
    MAX(CASE WHEN hsi.name = 'BONO SENIORS' THEN hsi.amount ELSE 0 END) AS "BONO SENIORS",
    MAX(CASE WHEN hsi.name = 'Bono septiembre' THEN hsi.amount ELSE 0 END) AS "Bono septiembre",
    MAX(CASE WHEN hsi.name = 'Bono Subgerente' THEN hsi.amount ELSE 0 END) AS "Bono Subgerente",
    MAX(CASE WHEN hsi.name = 'Bono Supervisores' THEN hsi.amount ELSE 0 END) AS "Bono Supervisores",
    MAX(CASE WHEN hsi.name = 'Bono Supervisores Noche' THEN hsi.amount ELSE 0 END) AS "Bono Supervisores Noche",
    MAX(CASE WHEN hsi.name = 'Bono Vacaciones' THEN hsi.amount ELSE 0 END) AS "Bono Vacaciones",
    MAX(CASE WHEN hsi.name = 'Bono Vendedores' THEN hsi.amount ELSE 0 END) AS "Bono Vendedores",
    MAX(CASE WHEN hsi.name = 'Bono Ventas' THEN hsi.amount ELSE 0 END) AS "Bono Ventas",
    MAX(CASE WHEN hsi.name = 'Gratificacion' THEN hsi.amount ELSE 0 END) AS "Gratificacion",
    MAX(CASE WHEN hsi.name = 'Movilizacion' THEN hsi.amount ELSE 0 END) AS "Movilizacion"
    -- ######################## FIN DE BONOS ESPECÍFICOS #########################

FROM rrhh_app.employees e
LEFT JOIN areas a 
    ON a.id = e.area_id AND a.cost_center = e.cost_center 
LEFT JOIN rrhh_app.employees jefe 
    ON e.rut_boss = jefe.rut
LEFT JOIN position_level pl 
    ON e.rut = pl.rut
LEFT JOIN rrhh_app.historical_settlement_items hsi 
    -- IMPORTANTE: Confirma que la unión entre empleados y sus items sea esta.
    ON e.id = hsi.ID_Persona 
    AND hsi.item_type = 'haber'

WHERE 
    e.status = 'activo'
    AND e.payment_method = 'Transferencia Bancaria'
    AND e.first_name IS NOT NULL
    AND pl.level IS NOT NULL
    AND e.rut NOT IN ('7.811.480-0', '4.775.647-2')

GROUP BY
    a.first_level_name, a.second_level_name, a.name, e.rut, e.full_name, e.gender, e.birthday,
    e.active_since, e.degree, pl.level, e.name_role, jefe.name_role, jefe.full_name, e.base_wage;