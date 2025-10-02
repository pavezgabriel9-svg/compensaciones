SELECT 
    e.full_name AS nombre,
    e.rut,
    e.birthday AS cumpleaños,
    MIN(a.name) AS área,              
    MIN(a.address) AS dirección,
    MIN(a.first_level_name) AS empresa,
    e.ctrlit_recinto AS marcaje
FROM employees e
JOIN areas a 
    ON e.cost_center = a.cost_center
WHERE e.status = "activo"
  AND e.payment_method = "transferencia bancaria"
GROUP BY 
    e.full_name, e.rut, e.birthday, e.ctrlit_recinto;