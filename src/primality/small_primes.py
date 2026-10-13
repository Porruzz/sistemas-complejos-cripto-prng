"""
Pre-filtro de división tentativa optimizado con números primos pequeños.
Elimina rápidamente (>88%) candidatos compuestos antes de pruebas modulares pesadas.
"""
from typing import List


def generate_small_primes(limit: int = 2000) -> List[int]:
    """Genera lista de primos hasta `limit` mediante la Criba de Eratóstenes."""
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for p in range(2, int(limit**0.5) + 1):
        if sieve[p]:
            for multiple in range(p * p, limit + 1, p):
                sieve[multiple] = False
    return [p for p, is_p in enumerate(sieve) if is_p]


# Lista precalculada de los 303 números primos hasta 1999
SMALL_PRIMES = generate_small_primes(2000)


def passes_small_primes_filter(n: int) -> bool:
    """
    Verifica rápidamente si n es divisible por algún primo menor a 2000.
    
    Retorna:
        True si no es divisible por ningún primo pequeño (candidato a primo),
        False si es compuesto demostrable.
    """
    if n < 2:
        return False
    # Verificación directa para números pequeños
    if n < 2000:
        return n in SMALL_PRIMES

    # Si es divisible por cualquiera de los primos de la criba, es compuesto
    for p in SMALL_PRIMES:
        if n % p == 0:
            return False
    return True
