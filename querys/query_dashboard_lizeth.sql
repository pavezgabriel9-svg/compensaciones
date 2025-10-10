WITH RECURSIVE jerarquia_gerente AS (
    -- Esta es la misma consulta recursiva de arriba
    SELECT
        rut AS gerente_rut,
        full_name AS gerente_nombre,
        rut AS empleado_rut
    FROM rrhh_app.employees
    WHERE rut IN(
	'12.474.901-8',
    '13.020.926-2',
    '13.190.934-9',
    '13.469.578-1',
    '13.679.960-6',
    '8.270.763-8',
    '8.954.496-3',
    '8.504.382-k',
    '8.957.970-8',
    '11.834.812-5',
    '8.851.361-4',
    '7.148.523-4',
    '11.843.532-k',
    '10.036.334-8',
    '10.172.861-7',
    '8.967.130-2'
)

    UNION ALL

    SELECT
        jg.gerente_rut,
        jg.gerente_nombre,
        e.rut AS empleado_rut
    FROM jerarquia_gerente jg
    JOIN rrhh_app.employees e ON e.rut_boss = jg.empleado_rut
    WHERE e.status = 'activo'
),

costos_por_empleado AS (
    -- Unimos la jerarquía con los datos de sueldo de cada empleado
    SELECT
        jg.gerente_rut,
        jg.gerente_nombre,
        emp.base_wage
    FROM jerarquia_gerente jg
    JOIN rrhh_app.employees emp ON jg.empleado_rut = emp.rut
    WHERE emp.status = 'activo' AND payment_method = "Transferencia Bancaria"
)

-- SELECT Final: Agrupamos por Gerente y sumamos los costos
SELECT
    gerente_nombre,
    COUNT(*) AS total_personas_en_la_gerencia,
    SUM(base_wage) AS costo_total_sueldos_base
FROM costos_por_empleado
GROUP BY gerente_rut, gerente_nombre
ORDER BY costo_total_sueldos_base DESC;