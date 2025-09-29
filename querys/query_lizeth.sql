WITH RECURSIVE subordinados AS (
    -- Nivel base: empleados que dependen directamente de un jefe
    SELECT
        jefes.rut AS jefe_rut,
        empleados.rut AS empleado_rut,
        1 AS nivel
    FROM rrhh_app.employees AS empleados
    JOIN rrhh_app.employees AS jefes ON empleados.rut_boss = jefes.rut
    WHERE empleados.status = 'activo' AND jefes.status = 'activo'

    UNION ALL

    -- Niveles recursivos: empleados que dependen indirectamente
    SELECT
        s.jefe_rut,
        e.rut,
        s.nivel + 1
    FROM subordinados s
    JOIN rrhh_app.employees e ON e.rut_boss = s.empleado_rut
    WHERE e.status = 'activo' AND s.nivel < 5
),

jefes_info AS (
    SELECT DISTINCT
        jefes.rut,
        jefes.full_name,
        jefes.name_role,
        jefes.rut_boss,
        jefes.cost_center,
        jefes.area_id,
        jefes.base_wage,
        jefe_superior.full_name AS reporta_a,
        jefe_superior.name_role AS cargo_jefe,
        areas.first_level_name AS empresa,
        areas.second_level_name AS seccion,
        areas.name AS area
    FROM rrhh_app.employees AS jefes
    LEFT JOIN rrhh_app.employees AS jefe_superior ON jefes.rut_boss = jefe_superior.rut
    LEFT JOIN rrhh_app.areas AS areas ON jefes.cost_center = areas.cost_center AND jefes.area_id = areas.id
    WHERE jefes.status = 'activo'
      AND (
          jefes.rut IN (SELECT DISTINCT jefe_rut FROM subordinados) -- Son jefes con subordinados
          OR jefes.name_role = 'Supervisor de Planta'               -- O son supervisores
      )
),

percentiles AS (
    SELECT
        rut,
        base_wage,
        PERCENT_RANK() OVER (ORDER BY base_wage) AS percentil
    FROM rrhh_app.employees
    WHERE status = 'activo'
)

SELECT
    ji.full_name AS nombre,
    ji.name_role AS cargo,
    COUNT(DISTINCT CASE WHEN subordinados.nivel = 1 THEN subordinados.empleado_rut END) AS personas_directas,
    COUNT(DISTINCT CASE WHEN subordinados.nivel > 1 THEN subordinados.empleado_rut END) AS personas_indirectas,
    ji.reporta_a,
    ji.cargo_jefe,
    ji.empresa,
    ji.seccion,
    ji.area,
    ROUND(p.percentil * 100, 2) AS percentil_sueldo_base
FROM jefes_info ji
LEFT JOIN subordinados ON ji.rut = subordinados.jefe_rut
LEFT JOIN percentiles p ON ji.rut = p.rut
GROUP BY ji.full_name, ji.name_role, ji.rut_boss,
         ji.reporta_a, ji.cargo_jefe,
         ji.empresa, ji.seccion, ji.area,
         p.percentil

ORDER BY personas_directas DESC, personas_indirectas DESC;