"""
Test de Primalidad Baillie-PSW (Miller-Rabin Base 2 + Test Fuerte de Lucas).
Es el estándar de la industria (utilizado en GMP, Mathematica, PARI/GP y Python sympy).
No tiene pseudoprimos conocidos menores a 2^64 ni en la literatura actual.
"""
from typing import Tuple
from src.core.interfaces import IPrimalityTester
from src.utils.math_utils import jacobi_symbol
from .small_primes import passes_small_primes_filter


class BailliePSWTester(IPrimalityTester):
    """
    Verificador de primalidad determinista práctico Baillie-PSW.
    Combina:
    1. Criba con números primos pequeños.
    2. Test de Miller-Rabin con base 2.
    3. Test Fuerte de Lucas con parámetros de Selfridge (Método A).
    """

    @property
    def name(self) -> str:
        return "Baillie-PSW (Deterministic Practical Hybrid)"

    def is_prime(self, candidate: int) -> bool:
        n = candidate
        if n < 2:
            return False
        if n in (2, 3):
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False

        if not passes_small_primes_filter(n):
            return False

        # Paso 1: Miller-Rabin en base 2
        if not self._miller_rabin_base2(n):
            return False

        # Si n es un cuadrado perfecto, es compuesto
        root = int(n ** 0.5)
        if root * root == n:
            return False

        # Paso 2: Test Fuerte de Lucas con Método A de Selfridge
        return self._strong_lucas_test(n)

    @staticmethod
    def _miller_rabin_base2(n: int) -> bool:
        """Paso Miller-Rabin exclusivamente en base 2."""
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        x = pow(2, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return True
            if x == 1:
                return False
        return False

    @classmethod
    def _strong_lucas_test(cls, n: int) -> bool:
        """Test Fuerte de Lucas con secuencia de Selfridge."""
        # Encontrar primer D en {5, -7, 9, -11, 13, ...} con Jacobi(D, n) == -1
        D = 5
        sign = 1
        while True:
            d_val = D * sign
            j = jacobi_symbol(d_val, n)
            if j == 0:
                # D divide a n
                return n == abs(d_val)
            if j == -1:
                D = d_val
                break
            D += 2
            sign = -sign
            if D > 1000:
                # Fallback seguro
                return True

        P = 1
        Q = (1 - D) // 4

        # Escribir n + 1 = 2^s * d
        d = n + 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1

        # Calcular U_d y V_d mod n mediante duplicación binaria
        U, V, Q_k = cls._lucas_sequence(d, P, Q, n)

        if U == 0 or V == 0:
            return True

        # Verificar si V_{d * 2^r} == 0 (mod n)
        for _ in range(1, s):
            V = (V * V - 2 * Q_k) % n
            Q_k = (Q_k * Q_k) % n
            if V == 0:
                return True

        return False

    @staticmethod
    def _lucas_sequence(k: int, P: int, Q: int, n: int) -> Tuple[int, int, int]:
        """Calcula U_k, V_k, Q^k mod n eficientemente en O(log k)."""
        U = 1
        V = P
        Q_k = Q
        k_bin = bin(k)[3:]  # omitir el bit más significativo '0b1'

        for bit in k_bin:
            U_next = (U * V) % n
            V_next = (V * V - 2 * Q_k) % n
            Q_next = (Q_k * Q_k) % n
            U, V, Q_k = U_next, V_next, Q_next

            if bit == '1':
                U_new = (P * U + V)
                if U_new % 2 != 0:
                    U_new += n
                U_new = (U_new // 2) % n

                V_new = (P * V + (P * P - 4 * Q) * U)
                if V_new % 2 != 0:
                    V_new += n
                V_new = (V_new // 2) % n

                Q_new = (Q_k * Q) % n
                U, V, Q_k = U_new, V_new, Q_new

        return U % n, V % n, Q_k % n
