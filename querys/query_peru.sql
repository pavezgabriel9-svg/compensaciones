SELECT
    empleado.full_name AS nombre_empleado,
    empleado.document_number AS dni_empleado,
    empleado.name_role AS cargo_empleado,
    empleado.base_wage AS sueldo_base,
    jefe.full_name AS nombre_jefe,
    jefe.name_role AS cargo_jefe,
	-- Calcula la edad en años
    TIMESTAMPDIFF(YEAR, empleado.birthday, CURDATE()) AS edad,
    -- Calcula el tiempo en la empresa en años
    TIMESTAMPDIFF(YEAR, empleado.active_since, CURDATE()) AS años_en_la_empresa,
    -- Calcula el tiempo en meses
    TIMESTAMPDIFF(MONTH, empleado.active_since, CURDATE()) AS meses_en_la_empresa
FROM
    rrhh_app.employees_peru AS empleado
LEFT JOIN
    rrhh_app.employees_peru AS jefe ON empleado.dni_boss = jefe.document_number
WHERE
    empleado.status = "activo";

