"""
Pipeline de Filtrado y Detección Masiva de Números Primos.
Aplica el Patrón Pipeline / Filter en etapas sucesivas de costo computacional creciente:
Etapa 1: Filtro de paridad
Etapa 2: Criba de factores pequeños (< 2000)
Etapa 3: Test de Miller-Rabin (k=40 rondas)
Etapa 4: Certificación Baillie-PSW
"""
import time
import math
from typing import List, Dict, Any, Optional, Callable
from .small_primes import passes_small_primes_filter
from .miller_rabin import MillerRabinTester
from .baillie_psw import BailliePSWTester


class PrimalityFilterPipeline:
    """
    Pipeline de filtrado de alto rendimiento para procesar lotes masivos (e.g. 10,000 números)
    y aislar los números primos de 40 cifras.
    """

    def __init__(self, mr_rounds: int = 40, verify_with_lucas: bool = True):
        self._mr_tester = MillerRabinTester(rounds=mr_rounds)
        self._lucas_tester = BailliePSWTester() if verify_with_lucas else None

    def test_single(self, number: int) -> bool:
        """Determina con máxima certeza si un número de 40 cifras es primo."""
        if number % 2 == 0:
            return number == 2
        if not passes_small_primes_filter(number):
            return False
        if not self._mr_tester.is_prime(number):
            return False
        if self._lucas_tester and not self._lucas_tester.is_prime(number):
            return False
        return True

    def process_batch(
        self,
        numbers: List[int],
        show_progress: bool = False,
        progress_callback: Optional[Callable[[int, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo sobre la colección de números.
        
        Args:
            numbers: Lista de enteros (e.g. 10,000 números de 40 cifras).
            show_progress: Si es True, imprime avance en consola.
            progress_callback: Callback opcional (procesados, total, primos_hallados).
            
        Returns:
            Dict con estadísticas completas y la lista de números primos encontrados.
        """
        total = len(numbers)
        if total == 0:
            return {"total": 0, "primes_found": [], "count": 0}

        t_start = time.perf_counter()

        rejected_even = 0
        rejected_small_primes = 0
        mr_candidates = 0
        primes_found: List[int] = []

        checkpoint = max(1, total // 10)

        for i, n in enumerate(numbers, start=1):
            # Etapa 1: Paridad
            if n % 2 == 0:
                rejected_even += 1
                if progress_callback:
                    progress_callback(i, total, len(primes_found))
                continue

            # Etapa 2: Primos pequeños
            if not passes_small_primes_filter(n):
                rejected_small_primes += 1
                if progress_callback:
                    progress_callback(i, total, len(primes_found))
                continue

            # Etapa 3: Miller-Rabin
            mr_candidates += 1
            if self._mr_tester.is_prime(n):
                # Etapa 4: Certificación opcional Baillie-PSW
                if self._lucas_tester is None or self._lucas_tester.is_prime(n):
                    primes_found.append(n)

            if progress_callback:
                progress_callback(i, total, len(primes_found))

            if show_progress and (i % checkpoint == 0 or i == total):
                elapsed = time.perf_counter() - t_start
                rate = i / elapsed if elapsed > 0 else 0
                pct = (i / total) * 100
                print(f"  [Primality Pipeline] Procesados: {i:,}/{total:,} ({pct:5.1f}%) | "
                      f"Primos hallados: {len(primes_found)} | Tasa: {rate:8.1f} num/s")

        t_total = time.perf_counter() - t_start

        # Análisis teórico según el Teorema de los Números Primos (PNT)
        # pi(x) ~ x / ln(x). Para x ~ 10^40, la densidad teórica es 1 / ln(10^40)
        digits = len(str(numbers[0])) if numbers else 40
        theoretical_density = 1.0 / (digits * math.log(10))
        empirical_density = len(primes_found) / total if total > 0 else 0.0

        return {
            "total_analyzed": total,
            "primes_found_count": len(primes_found),
            "primes_list": primes_found,
            "rejected_even_count": rejected_even,
            "rejected_small_primes_count": rejected_small_primes,
            "miller_rabin_candidates_count": mr_candidates,
            "elapsed_seconds": round(t_total, 4),
            "throughput_num_per_sec": round(total / t_total if t_total > 0 else 0, 2),
            "empirical_density_pct": round(empirical_density * 100, 4),
            "theoretical_density_pct": round(theoretical_density * 100, 4),
            "pnt_ratio": round(empirical_density / theoretical_density, 3) if theoretical_density > 0 else 0.0
        }
