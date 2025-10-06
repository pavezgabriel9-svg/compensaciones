SELECT
	Pay_Period,
	RUT AS rut,
	Liquido_a_Pagar, 
    Ingreso_Bruto
FROM historical_settlements
WHERE Pay_Period >= '2018-01-01'
ORDER BY rut, Pay_Period;