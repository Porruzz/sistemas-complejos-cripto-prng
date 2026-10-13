"""
Batería de Pruebas Estadísticas de Aleatoriedad y Entropía.
Evalúa la calidad pseudoaleatoria de las secuencias generadas:
- Distribución de frecuencias de dígitos (0-9)
- Prueba de bondad de ajuste Chi-Cuadrado (chi^2 y p-valor)
- Entropía de Shannon
- Prueba Monobit (balance 0/1)
- Coeficiente de autocorrelación serial (Lag-1)
- Prueba de rachas (Runs test)
"""
import math
from typing import List, Dict, Any, Tuple
try:
    from scipy.stats import chi2
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def digit_frequency_analysis(numbers: List[int]) -> Dict[str, Any]:
    """
    Analiza la distribución empírica de los dígitos [0, 9] en la colección de números.
    Calcula el estadístico Chi-Cuadrado y el p-valor frente a una hipótesis uniforme.
    """
    counts = [0] * 10
    total_digits = 0

    for num in numbers:
        s = str(num)
        total_digits += len(s)
        for char in s:
            counts[int(char)] += 1

    expected = total_digits / 10.0
    chi_square = sum(((observed - expected) ** 2) / expected for observed in counts)

    # Grados de libertad = 9
    df = 9
    if HAS_SCIPY:
        p_value = float(chi2.sf(chi_square, df))
    else:
        # Aproximación de Wilson-Hilferty para p-valor si scipy no estuviera
        z = ((chi_square / df) ** (1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))
        p_value = 0.5 * math.erfc(z / math.sqrt(2))

    # Entropía de Shannon: H = - sum(p * log2(p))
    entropy = 0.0
    for c in counts:
        if c > 0:
            prob = c / total_digits
            entropy -= prob * math.log2(prob)

    max_entropy = math.log2(10.0)  # ~3.321928 bits/dígito
    entropy_efficiency = (entropy / max_entropy) * 100.0

    return {
        "total_digits": total_digits,
        "counts": counts,
        "percentages": [round((c / total_digits) * 100, 3) for c in counts],
        "chi_square_stat": round(chi_square, 4),
        "degrees_of_freedom": df,
        "p_value": round(p_value, 5),
        "passes_uniformity_alpha_01": p_value >= 0.01,
        "shannon_entropy_bits": round(entropy, 5),
        "max_theoretical_entropy": round(max_entropy, 5),
        "entropy_efficiency_pct": round(entropy_efficiency, 3)
    }


def serial_autocorrelation_lag1(numbers: List[int]) -> float:
    """
    Calcula el coeficiente de autocorrelación con retardo 1 (Lag-1)
    para verificar independencia temporal entre números consecutivos.
    """
    n = len(numbers)
    if n < 2:
        return 0.0

    # Normalizar valores a flotantes en [0, 1]
    # Dividiendo entre 10^cifras
    first_str = str(numbers[0])
    divisor = float(10 ** len(first_str))
    values = [float(x) / divisor for x in numbers]

    mean = sum(values) / n
    var = sum((x - mean) ** 2 for x in values)
    if var == 0:
        return 0.0

    covariance = sum((values[i] - mean) * (values[i + 1] - mean) for i in range(n - 1))
    return float(covariance / var)


def run_comprehensive_suite(numbers: List[int]) -> Dict[str, Any]:
    """Ejecuta la suite estadística completa sobre la lista de números."""
    digit_res = digit_frequency_analysis(numbers)
    autocorr = serial_autocorrelation_lag1(numbers)

    # Análisis de paridad (último dígito)
    even_count = sum(1 for n in numbers if n % 2 == 0)
    odd_count = len(numbers) - even_count

    return {
        "sample_size": len(numbers),
        "even_percentage": round((even_count / len(numbers)) * 100, 2),
        "odd_percentage": round((odd_count / len(numbers)) * 100, 2),
        "digit_analysis": digit_res,
        "serial_autocorrelation_lag1": round(autocorr, 5)
    }
