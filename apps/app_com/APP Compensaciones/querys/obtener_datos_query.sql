SELECT
    e.person_id,
    e.rut,
    e.full_name,
    COALESCE(e.gender, 'N/A') AS gender,
    e.area_id,
    COALESCE(e.contract_type, 'N/A') AS contract_type,
    e.active_since,
    -- Historial desde job_history
    eh.start_date,
    eh.end_date,
    eh.historical_role,
    eh.base_wage,
    -- Empresa, división y área
    COALESCE(a.first_level_name, CONCAT('empresa ', a.first_level_id)) AS company_name,
    COALESCE(a.second_level_name, CONCAT('División ', a.second_level_id)) AS division_name,
    COALESCE(a.name, CONCAT('Área ', e.area_id)) AS area_name,
    -- Jefatura
    jefe.full_name AS boss_name,
    pl.level AS level
FROM
    job_history eh
JOIN
    employees e ON eh.person_rut = e.rut
LEFT JOIN
    areas a ON e.area_id = a.id
LEFT JOIN
    employees jefe ON eh.boss_rut = jefe.rut
LEFT JOIN
    position_level pl ON e.rut = pl.rut
WHERE
    e.status = 'activo' AND eh.start_date >= '2018-01-01'
ORDER BY
    e.full_name, eh.start_date;



