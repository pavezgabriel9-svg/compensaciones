# valores por defecto
parametros_default = {
    "ingreso_minimo": 529_000,
    "valor_uf": 39_149,
    "tope_imponible_uf": 87.8,
    "tasa_afp": 0.1049,
    "tasa_salud": 0.07,
    "tasa_cesant": 0.006,
    "factor_gratificacion": 4.75,
    "porcentaje_gratificacion": 0.25
}

# Tramos de impuesto por defecto
tramos_default = [
    {"desde": 0,          "hasta": 926734.50,  "tasa": 0.00, "rebaja":       0.0},
    {"desde": 926734.51,  "hasta": 2059410.00, "tasa": 0.04, "rebaja":   37069.38},
    {"desde": 2059410.01, "hasta": 3432350.00, "tasa": 0.08, "rebaja":  119445.78},
    {"desde": 3432350.01, "hasta": 4805290.00, "tasa": 0.135,"rebaja":  308225.03},
    {"desde": 4805290.01, "hasta": 6178230.00, "tasa": 0.23, "rebaja":  764727.58},
    {"desde": 6178230.01, "hasta": 8237640.00, "tasa": 0.304,"rebaja": 1221916.60},
    {"desde": 8237640.01, "hasta": 21280570.00,"tasa": 0.35, "rebaja": 1600848.04},
    {"desde": 21280570.01,"hasta": float('inf'),"tasa": 0.40,"rebaja": 2664876.54},
]