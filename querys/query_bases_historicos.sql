SELECT
	e.person_id,
	e.rut,
	e.full_name AS Nombre,
	COALESCE(e.gender, 'N/A') AS Género,
	e.area_id AS ID_Area,
	COALESCE(e.contract_type, 'N/A') AS Tipo_Contrato,
	e.active_since,

	-- Historial desde job_history
	eh.start_date,
	eh.end_date,
	eh.historical_role AS Cargo_Actual,
	eh.base_wage AS Sueldo_Base,

	-- Área
	COALESCE(a.name, CONCAT('Área ', e.area_id)) AS Nombre_Area,

	-- Jefatura
	jefe.full_name AS Nombre_Jefe

FROM job_history eh
JOIN employees e
	ON eh.person_rut = e.rut
LEFT JOIN areas a
	ON e.area_id = a.id
LEFT JOIN employees jefe
	ON eh.boss_rut = jefe.rut

WHERE e.status = 'activo' 
	AND eh.start_date >= '2018-01-01'
ORDER BY e.full_name, eh.start_date;
            