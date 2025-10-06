SELECT
    rut,
    email,
    phone,
    gender,
    birthday,
    university,
    nationality,
    degree
FROM
    employees
WHERE
    status = 'activo';