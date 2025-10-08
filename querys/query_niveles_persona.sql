SELECT 
    e.rut,
    e.full_name,
    e.name_role,
    p.level,
    e.base_wage
FROM rrhh_app.employees e
JOIN rrhh_app.position_level p 
    ON e.rut = p.rut
WHERE status = 'activo'
ORDER BY p.level, e.base_wage;
