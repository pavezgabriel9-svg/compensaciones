WITH SalaryChanges AS (
  SELECT
    person_rut,
    start_date,
    base_wage,
    LAG(base_wage) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_wage_raw
  FROM job_history
  WHERE start_date >= '2019-01-01'
),
DistinctSalaryPeriods AS (
  SELECT
    person_rut,
    start_date,
    base_wage
  FROM SalaryChanges
  WHERE prev_wage_raw IS NULL  -- Primera entrada
     OR base_wage <> prev_wage_raw  -- Cambio de salario
),
WithLags AS (
  SELECT
    person_rut,
    start_date,
    base_wage,
    LAG(base_wage) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_wage,
    LAG(start_date) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_start_date
  FROM DistinctSalaryPeriods
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
    TIMESTAMPDIFF(MONTH, prev_start_date, start_date) AS meses_entre_aumentos
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
RankedResults AS (
  SELECT
    e.rut,
    e.full_name AS nombre,
    e.active_since AS ingreso,
    e.birthday as nacimiento,
    e.name_role AS cargo,
    jefe.full_name AS nombre_jefe, -- Nombre del Jefe
    a.name AS area,               -- Área
    a.second_level_name AS division, -- División
    w.start_date,
    w.base_wage AS base,
    w.prev_wage AS base_previo,
    w.prev_start_date AS fecha_aumento_previo,
    w.variacion_salarial_porcentual,
    w.meses_entre_aumentos,
    ROUND(a_avg.promedio_aumentos, 2) AS promedio_aumentos,
    TIMESTAMPDIFF(MONTH, w.start_date, CURDATE()) AS meses_sin_aumento,
    ROW_NUMBER() OVER (PARTITION BY e.rut ORDER BY w.start_date DESC) AS rn
  FROM employees e
  INNER JOIN WithVariations w ON e.rut = w.person_rut
  LEFT JOIN AvgIncrease a_avg ON e.rut = a_avg.person_rut
  
  -- JOIN para obtener el nombre del jefe
  LEFT JOIN employees jefe ON e.rut_boss = jefe.rut 
  
  -- JOIN para obtener el área y la división
  LEFT JOIN areas a ON e.cost_center = a.cost_center
  
  WHERE e.status = 'activo' -- AND e.rut = "19.420.469-8"
)
SELECT
  rut,
  nombre,
  nombre_jefe,
  area,       
  division,   
  cargo,
  nacimiento,
  ingreso,
  base,
  base_previo,
  fecha_aumento_previo,
  variacion_salarial_porcentual,
  meses_entre_aumentos,
  promedio_aumentos,
  meses_sin_aumento
FROM RankedResults
WHERE rn = 1
ORDER BY meses_sin_aumento DESC;