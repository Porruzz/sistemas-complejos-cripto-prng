"""
Test de Primalidad Probabilístico de Miller-Rabin de alta precisión.
Garantiza probabilidad de error menor a 4^(-k) (para k=40, P_error < 10^(-24)).
"""
import random
from typing import Optional, List
from src.core.interfaces import IPrimalityTester
from .small_primes import passes_small_primes_filter


class MillerRabinTester(IPrimalityTester):
    """
    Implementación del Test de Miller-Rabin para enteros de precisión arbitraria.
    
    Algoritmo:
    Dado n impar > 2, escribe n - 1 = 2^s * d con d impar.
    Para una base aleatoria a in [2, n - 2]:
        Si a^d = 1 (mod n) o a^(d * 2^r) = n - 1 (mod n) para algún r in [0, s - 1],
        el candidato pasa la ronda (pseudoprimo fuerte en base a).
    Si falla para alguna base, n es comprobadamente compuesto.
    """

    # Primeras bases primas conocidas para determinismo en rangos menores
    DETERMINISTIC_BASES_64 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

    def __init__(self, rounds: int = 40):
        self._rounds = max(10, rounds)

    @property
    def name(self) -> str:
        return f"Miller-Rabin (Rounds={self._rounds})"

    @property
    def rounds(self) -> int:
        return self._rounds

    def is_prime(self, candidate: int) -> bool:
        """
        Evalúa si el candidato es primo ejecutando el prefiltro y `rounds` rondas de Miller-Rabin.
        """
        n = candidate
        if n < 2:
            return False
        if n in (2, 3):
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False

        # Pre-filtro con primos pequeños
        if not passes_small_primes_filter(n):
            return False

        # Descomponer n - 1 = 2^s * d con d impar
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1

        # Para números de 64 bits o menos, las 12 primeras bases primas son 100% deterministas
        if n < (1 << 64):
            bases = [b for b in self.DETERMINISTIC_BASES_64 if b < n]
            for a in bases:
                if not self._witness(a, n, d, s):
                    return False
            return True

        # Para números grandes de 40 cifras (aprox 133 bits), probar base 2 y luego aleatorias
        if not self._witness(2, n, d, s):
            return False

        for _ in range(self._rounds - 1):
            a = random.randrange(2, n - 1)
            if not self._witness(a, n, d, s):
                return False

        return True

    @staticmethod
    def _witness(a: int, n: int, d: int, s: int) -> bool:
        """
        Evalúa si la base 'a' certifica que 'n' es un probable primo fuerte.
        Retorna True si pasa la ronda, False si 'n' es compuesto.
        """
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True

        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return True
            if x == 1:
                return False

        return False
