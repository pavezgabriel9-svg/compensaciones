WITH SalaryChanges AS (
    SELECT
        t1.person_rut,
        t1.start_date,
        t1.base_wage,
        -- Simulación de LAG() con SELF JOIN
        (
            SELECT t2.base_wage
            FROM job_history t2
            WHERE t2.person_rut = t1.person_rut
              AND t2.start_date < t1.start_date
            ORDER BY t2.start_date DESC
            LIMIT 1
        ) AS prev_wage_raw
    FROM job_history t1
    WHERE t1.start_date >= '2019-01-01'
),
DistinctSalaryPeriods AS (
    SELECT
        person_rut,
        start_date,
        base_wage
    FROM SalaryChanges
    WHERE prev_wage_raw IS NULL
      OR base_wage <> prev_wage_raw
),
WithLags AS (
    SELECT
        t1.person_rut,
        t1.start_date,
        t1.base_wage,
        -- Simulación de LAG(base_wage)
        (
            SELECT t2.base_wage
            FROM DistinctSalaryPeriods t2
            WHERE t2.person_rut = t1.person_rut
              AND t2.start_date < t1.start_date
            ORDER BY t2.start_date DESC
            LIMIT 1
        ) AS prev_wage,
        -- Simulación de LAG(start_date)
        (
            SELECT t2.start_date
            FROM DistinctSalaryPeriods t2
            WHERE t2.person_rut = t1.person_rut
              AND t2.start_date < t1.start_date
            ORDER BY t2.start_date DESC
            LIMIT 1
        ) AS prev_start_date
    FROM DistinctSalaryPeriods t1
),
WithVariations AS (
    SELECT
        person_rut,
        start_date,
        base_wage,
        prev_wage,
        prev_start_date,
        CASE
            WHEN prev_wage > 0 THEN ROUND((base_wage - prev_wage) * 100.0 / prev_wage, 2)
            ELSE 0
        END AS variacion_salarial_porcentual,
        -- Reemplazo de TIMESTAMPDIFF(MONTH, ...) por cálculo manual
        (YEAR(start_date) * 12 + MONTH(start_date)) - (YEAR(prev_start_date) * 12 + MONTH(prev_start_date)) AS meses_entre_aumentos
    FROM WithLags
),
AvgIncrease AS (
    SELECT
        person_rut,
        AVG(variacion_salarial_porcentual) AS promedio_aumentos
    FROM WithVariations
    WHERE prev_wage IS NOT NULL
    GROUP BY person_rut
),
-- Los CTEs EmployeeAreaRank y EmployeeInfo requieren reemplazar ROW_NUMBER().
-- Para simplificar, asumiremos que EmployeeAreaRank no necesita el rankeo si no hay duplicados *reales*
-- o usaremos el mismo patrón de subconsulta. Usaremos el CTE 'AreaFilter' para limpiar el duplicado.
AreaFilter AS (
    SELECT
        e.rut,
        e.full_name,
        boss.full_name AS nombre_jefe,
        ar.name AS area,
        ar.second_level_name AS division,
        ar.id as area_id -- Usamos el ID para identificar la "primera" área
    FROM employees e
    LEFT JOIN employees boss ON e.id_boss = boss.id
    LEFT JOIN areas ar ON e.cost_center = ar.cost_center
    WHERE e.status = 'activo'
),
EmployeeInfo AS (
    SELECT
        af1.rut,
        af1.full_name,
        af1.nombre_jefe,
        af1.area,
        af1.division
    FROM AreaFilter af1
    WHERE af1.area_id = ( -- Filtro para seleccionar la primera area por RUT
        SELECT MIN(af2.area_id)
        FROM AreaFilter af2
        WHERE af2.rut = af1.rut
    )
)
SELECT
    ei.rut,
    ei.full_name AS nombre,
    ei.nombre_jefe,
    ei.area,
    ei.division,
    w.start_date,
    w.prev_start_date,
    w.base_wage,
    w.prev_wage,
    w.variacion_salarial_porcentual,
    w.meses_entre_aumentos,
    ROUND(a.promedio_aumentos, 2) AS promedio_aumentos_historico,
    -- Reemplazo de TIMESTAMPDIFF(MONTH, ...) por cálculo manual
    (YEAR(CURDATE()) * 12 + MONTH(CURDATE())) - (YEAR(w.start_date) * 12 + MONTH(w.start_date)) AS meses_sin_aumento
FROM EmployeeInfo ei
INNER JOIN WithVariations w ON ei.rut = w.person_rut
LEFT JOIN AvgIncrease a ON ei.rut = a.person_rut
ORDER BY ei.rut, w.start_date;