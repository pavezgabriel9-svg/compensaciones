WITH SalaryChanges AS (
  SELECT
    person_rut,
    start_date,
    base_wage,
    LAG(base_wage) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_wage_raw
  FROM employees_jobs
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
  -- Recalcular LAG después del filtrado
  SELECT
    person_rut,
    start_date,
    base_wage,
    LAG(base_wage) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_wage,
    LAG(start_date) OVER (PARTITION BY person_rut ORDER BY start_date) AS prev_start_date
  FROM DistinctSalaryPeriods
)
SELECT
  e.rut,
  e.full_name AS nombre,
  w.start_date,
  w.base_wage,
  w.prev_wage,
  w.prev_start_date,
  CASE
    WHEN w.prev_wage > 0 THEN ROUND((w.base_wage - w.prev_wage) * 100.0 / w.prev_wage, 2)
    ELSE 0
  END AS variacion_salarial_porcentual,
  CASE
    WHEN w.prev_wage IS NOT NULL THEN
      TIMESTAMPDIFF(MONTH, w.prev_start_date, w.start_date)
    ELSE 0
  END AS meses_entre_aumentos
FROM employees e
INNER JOIN WithLags w ON e.rut = w.person_rut
WHERE e.status = 'activo'
ORDER BY w.start_date;
