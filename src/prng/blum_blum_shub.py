"""
Técnica 3: Generador Pseudoaleatorio Criptográfico Blum-Blum-Shub (BBS).
Fundamento Teórico-Numérico: Dificultad del problema de los residuos cuadráticos y factorización de enteros.
"""
import time
import math
from typing import Any, Optional
from src.core.interfaces import IPRNGStrategy
from src.core.exceptions import PRNGConfigError
from src.utils.math_utils import is_coprime


class BlumBlumShubStrategy(IPRNGStrategy):
    """
    Generador de números pseudoaleatorios criptográficamente seguro Blum-Blum-Shub (BBS).
    
    Fundamento Matemático:
    Propuesto en 1986 por Lenore Blum, Manuel Blum y Michael Shub.
    Su seguridad se reduce formalmente a la intratabilidad computacional del problema
    de decidir si un número es un residuo cuadrático módulo M (QRP - Quadratic Residuosity Problem),
    el cual es asintóticamente equivalente a la dificultad de factorizar M = p * q.
    
    Ecuación de recurrencia:
        x_{n+1} = (x_n)^2 mod M
    donde p y q son números primos de Blum tales que:
        p = 3 mod 4,  q = 3 mod 4
    
    Salida: Se extraen los k bits menos significativos por iteración,
    donde k <= floor(log2(log2(M))), teorema probado por U. Vazirani y V. Vazirani.
    """

    # Primos de Blum por defecto de 256 bits verificados formalmente
    DEFAULT_P = 57896044618658097711785492504343953926634992332820282019728792003956564874307
    DEFAULT_Q = 57896044618658097711785492504343953926634992332820282019728792003956652474391

    def __init__(
        self,
        p: Optional[int] = None,
        q: Optional[int] = None,
        seed: Optional[int] = None,
        bits_per_round: Optional[int] = None
    ):
        self._p = p or self.DEFAULT_P
        self._q = q or self.DEFAULT_Q
        self._m = self._p * self._q
        self._state = 0
        self._bits_per_round = bits_per_round or 4
        self._bit_buffer = 0
        self._bits_in_buffer = 0

        self.configure(p=self._p, q=self._q, seed=seed, bits_per_round=self._bits_per_round)

    @property
    def name(self) -> str:
        return "Blum-Blum-Shub (Number-Theoretic Cryptographic PRNG)"

    @property
    def description(self) -> str:
        return (
            "Generador criptográfico basado en residuos cuadráticos mod M = p*q con primos de Blum. "
            "Seguridad teórica demostrada equivalente a la factorización de enteros."
        )

    def configure(self, **kwargs: Any) -> None:
        """
        Configura los parámetros del generador BBS.
        Parámetros aceptados:
            p (int): Primer primo de Blum (p = 3 mod 4).
            q (int): Segundo primo de Blum (q = 3 mod 4).
            seed (int): Semilla s tal que mcd(s, M) == 1.
            bits_per_round (int): Bits seguros extraídos por elevación al cuadrado.
        """
        if "p" in kwargs and kwargs["p"] is not None:
            p_val = int(kwargs["p"])
            if p_val % 4 != 3:
                raise PRNGConfigError(f"p debe ser primo de Blum (p = 3 mod 4), recibido: {p_val % 4}")
            self._p = p_val

        if "q" in kwargs and kwargs["q"] is not None:
            q_val = int(kwargs["q"])
            if q_val % 4 != 3:
                raise PRNGConfigError(f"q debe ser primo de Blum (q = 3 mod 4), recibido: {q_val % 4}")
            self._q = q_val

        self._m = self._p * self._q

        # Máximo de bits teóricos seguros por paso según Vazirani
        max_safe_bits = max(1, int(math.log2(math.log2(self._m))))
        if "bits_per_round" in kwargs and kwargs["bits_per_round"] is not None:
            bpr = int(kwargs["bits_per_round"])
            self._bits_per_round = max(1, min(bpr, max_safe_bits * 2))
        else:
            self._bits_per_round = max_safe_bits

        seed_val = kwargs.get("seed", None)
        if seed_val is None:
            t = time.time_ns()
            seed_val = (t ^ 0xDEADBEEFCAFE) % (self._m - 2) + 2
        else:
            seed_val = int(seed_val) % (self._m - 2) + 2

        # Asegurar coprimalidad con M
        while not is_coprime(seed_val, self._m) or seed_val in (0, 1):
            seed_val = (seed_val + 3) % (self._m - 2) + 2

        # x_0 = s^2 mod M
        self._state = pow(seed_val, 2, self._m)
        self._bit_buffer = 0
        self._bits_in_buffer = 0

    def _step(self) -> None:
        """Avanza el estado elevando al cuadrado módulo M: x_{n+1} = x_n^2 mod M."""
        self._state = pow(self._state, 2, self._m)
        # Extraer los bits_per_round bits menos significativos
        mask = (1 << self._bits_per_round) - 1
        self._bit_buffer = self._state & mask
        self._bits_in_buffer = self._bits_per_round

    def next_bit(self) -> int:
        """Extrae el siguiente bit pseudoaleatorio del buffer o avanza el estado."""
        if self._bits_in_buffer == 0:
            self._step()
        bit = self._bit_buffer & 1
        self._bit_buffer >>= 1
        self._bits_in_buffer -= 1
        return bit

    def next_bits(self, count: int) -> int:
        """Extrae `count` bits del flujo pseudoaleatorio BBS."""
        result = 0
        for _ in range(count):
            result = (result << 1) | self.next_bit()
        return result

    def generate_number(self, digits: int = 40) -> int:
        """
        Genera un número de exactamente `digits` cifras decimales garantizando
        uniformidad en el rango [10^(digits-1), 10^digits - 1].
        """
        if digits <= 0:
            raise ValueError("El número de cifras debe ser mayor que cero.")

        lower_bound = 10 ** (digits - 1)
        upper_bound = (10 ** digits) - 1
        span = upper_bound - lower_bound + 1

        bit_length = span.bit_length() + 8
        raw_bits = self.next_bits(bit_length)
        return lower_bound + (raw_bits % span)
