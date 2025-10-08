SELECT 
    e.base_wage,
    e.full_name,
    e.rut,
    e.birthday,
    e.active_since,
    e.name_role,
    e.cost_center,
    e.id_boss,
    e.contract_type,
    e.nationality,
    e.civil_status,
    e.district,
    e.degree,
    p.level 
FROM rrhh_app.employees e
JOIN rrhh_app.position_level p
    ON e.rut = p.rut
WHERE 
    e.status = "activo"
    AND level IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14)


    -- AND p.level = 4;
    -- AND name_role IN ("Operario", "Operario Almacenamiento y Gestión de Residuos", 'Asistente De Bodega', 'Asistente De Servicios Generales', 'Ayudante De Bodega','Peoneta');
    -- AND level IN (1, 2, 3, 4);