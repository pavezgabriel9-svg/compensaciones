WITH RECURSIVE subordinados AS (
    SELECT
        jefes.rut AS jefe_rut,
        empleados.rut AS empleado_rut,
        1 AS nivel
    FROM rrhh_app.employees AS empleados
    JOIN rrhh_app.employees AS jefes ON empleados.rut_boss = jefes.rut
    WHERE empleados.status = 'activo' AND jefes.status = 'activo'


    UNION ALL

    SELECT
        s.jefe_rut,
        e.rut,
        s.nivel + 1
    FROM subordinados s
    JOIN rrhh_app.employees e ON e.rut_boss = s.empleado_rut
    WHERE e.status = 'activo' AND s.nivel < 5
)

SELECT DISTINCT
    j.name_role AS cargo,
    j.full_name AS nombre,
    j.email AS correo
FROM rrhh_app.employees j
WHERE j.status = 'activo'
  AND j.rut IN (SELECT jefe_rut FROM subordinados)
  AND email NOT LIKE '%@cramer.cl%'
  AND email NOT LIKE '%@sabores.cl%'
ORDER BY j.name_role, j.full_name;
