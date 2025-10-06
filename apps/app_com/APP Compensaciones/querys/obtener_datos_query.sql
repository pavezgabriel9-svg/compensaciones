SELECT
	e.person_id,
	e.rut,
	e.full_name,
	COALESCE(e.gender, 'N/A'),
	e.area_id,
	COALESCE(e.contract_type, 'N/A'),
	e.active_since,

	-- Historial desde job_history
	eh.start_date,
	eh.end_date,
	eh.role_name, -- historical_role
	eh.base_wage,

		-- empresa
	COALESCE(a.first_level_name, CONCAT('empresa ', a.first_level_id)) AS company_name,
		-- división
	COALESCE(a.second_level_name, CONCAT('División', a.second_level_name)) AS division_name,
		-- área
	COALESCE(a.name, CONCAT('Área ', e.area_id)) AS area_name,
    
	-- Jefatura
	jefe.full_name AS boss_name

FROM employees_jobs eh -- job_history  
JOIN employees e
	ON eh.person_rut = e.rut
LEFT JOIN areas a
	ON e.area_id = a.id
LEFT JOIN employees jefe
	ON eh.boss_rut = jefe.rut

WHERE e.status = 'activo' AND eh.start_date >= '2018-01-01'
ORDER BY e.full_name, eh.start_date;