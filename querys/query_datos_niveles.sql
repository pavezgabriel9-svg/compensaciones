WITH salarios AS (
    SELECT 
        p.level AS position_level,
        e.base_wage,
        PERCENT_RANK() OVER (PARTITION BY p.level ORDER BY e.base_wage) AS pr,
        e.status
    FROM rrhh_app.employees e
    JOIN rrhh_app.position_level p 
        ON e.name_role = p.name_role
),
percentiles AS (
    SELECT
        position_level,
        base_wage,
        pr,
        ROW_NUMBER() OVER (PARTITION BY position_level ORDER BY ABS(pr - 0.25)) AS rn25,
        ROW_NUMBER() OVER (PARTITION BY position_level ORDER BY ABS(pr - 0.50)) AS rn50,
        ROW_NUMBER() OVER (PARTITION BY position_level ORDER BY ABS(pr - 0.75)) AS rn75
    FROM salarios
    WHERE status = "activo"
)
SELECT 
    p.position_level,
    COUNT(*) AS total_empleados,
    ROUND(AVG(p.base_wage), 0) AS sueldo_promedio,
    ROUND(STDDEV(p.base_wage), 2) AS desviacion_estandar,
    MIN(p.base_wage) AS sueldo_min,
    MAX(CASE WHEN rn25 = 1 THEN base_wage END) AS p25,
    MAX(CASE WHEN rn50 = 1 THEN base_wage END) AS p50,
    MAX(CASE WHEN rn75 = 1 THEN base_wage END) AS p75,
    MAX(p.base_wage) AS sueldo_max
FROM percentiles p
GROUP BY p.position_level
ORDER BY p.position_level;


