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
    e.base_wage AS sueldo_base
FROM rrhh_app.employees e
LEFT JOIN areas a
	ON a.id = e.area_id
    AND a.cost_center = e.cost_center 
LEFT JOIN employees jefe 
	ON e.rut_boss = jefe.rut
LEFT JOIN position_level pl
	ON e.rut = pl.rut
WHERE e.status = 'activo'
	AND e.payment_method = 'Transferencia Bancaria'
    AND e.first_name IS NOT null
	AND pl.level IS NOT NULL
	-- AND e.rut = "8.967.130-2"
    AND e.rut NOT IN ("7.811.480-0", "4.775.647-2");

    