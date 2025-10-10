WITH RECURSIVE jerarquia_gerente AS (
    -- 1. Nivel base o "Ancla": Seleccionamos al Gerente que será nuestro punto de partida.
    SELECT
        rut AS gerente_rut,
        full_name AS gerente_nombre,
        rut AS empleado_rut,
        0 AS nivel 
    FROM rrhh_app.employees
    WHERE rut = '7.148.523-4'
    
    UNION ALL

    SELECT
        jg.gerente_rut,
        jg.gerente_nombre,
        e.rut AS empleado_rut,
        jg.nivel + 1 -- Aumentamos el nivel a medida que descendemos
    FROM jerarquia_gerente jg
    JOIN rrhh_app.employees e ON e.rut_boss = jg.empleado_rut -- La unión es hacia abajo
    WHERE e.status = 'activo' and payment_method = "Transferencia Bancaria"
)
SELECT
    jg.gerente_nombre AS gerencia,
    jg.nivel as nivel,
    emp.full_name AS nombre_empleado,
    emp.name_role AS cargo_empleado,
    emp.base_wage AS sueldo_base,
    ar.name AS area
FROM jerarquia_gerente jg
JOIN rrhh_app.employees emp ON jg.empleado_rut = emp.rut
LEFT JOIN rrhh_app.areas ar ON emp.cost_center = ar.cost_center AND emp.area_id = ar.id
ORDER BY jg.nivel, nombre_empleado;