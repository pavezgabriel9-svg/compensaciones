"""
    Módulo de servicios para la calculadora de sueldos.
"""

def formato_chile_sueldo(current_value: str) -> str:
    try:
        numeric_value = int("".join(filter(str.isdigit, current_value)))
        formatted_value = f"{numeric_value:,}".replace(",", ".")
        return formatted_value
    except (ValueError, TypeError):
        return ""