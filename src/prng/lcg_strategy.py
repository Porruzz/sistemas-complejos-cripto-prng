"""
Técnica Adicional (Benchmark Comparativo): Generador Congruencial Lineal de 128 bits (Knuth/MMIX LCG).
"""
import time
from typing import Any, Optional
from src.core.interfaces import IPRNGStrategy


class LCGStrategy(IPRNGStrategy):
    """
    Generador Congruencial Lineal de 128 bits con parámetros de Knuth (MMIX extendido).
    X_{n+1} = (a * X_n + c) mod 2^128.
    """

    MOD_128 = 1 << 128
    MASK_128 = (1 << 128) - 1

    # Multiplicador y constante aditiva de Knuth para 128 bits
    DEFAULT_A = 2862933555777941757011406699047334709
    DEFAULT_C = 3037000493

    def __init__(
        self,
        seed: Optional[int] = None,
        multiplier: Optional[int] = None,
        increment: Optional[int] = None
    ):
        self._a = multiplier or self.DEFAULT_A
        self._c = increment or self.DEFAULT_C
        self._state = 0
        self.configure(seed=seed, multiplier=self._a, increment=self._c)

    @property
    def name(self) -> str:
        return "128-bit Linear Congruential Generator (LCG)"

    @property
    def description(self) -> str:
        return "Generador congruencial de gran periodo (2^128) con parámetros de Donald Knuth."

    def configure(self, **kwargs: Any) -> None:
        if "multiplier" in kwargs and kwargs["multiplier"] is not None:
            self._a = int(kwargs["multiplier"]) & self.MASK_128
        if "increment" in kwargs and kwargs["increment"] is not None:
            self._c = int(kwargs["increment"]) & self.MASK_128

        seed_val = kwargs.get("seed", None)
        if seed_val is None:
            seed_val = time.time_ns()
        self._state = int(seed_val) & self.MASK_128

    def next_bit(self) -> int:
        self._state = (self._a * self._state + self._c) & self.MASK_128
        # Extraer bit de orden superior (mayor aleatoriedad que bits bajos en LCG)
        return (self._state >> 127) & 1

    def next_bits(self, count: int) -> int:
        result = 0
        for _ in range(count):
            result = (result << 1) | self.next_bit()
        return result

    def generate_number(self, digits: int = 40) -> int:
        lower_bound = 10 ** (digits - 1)
        upper_bound = (10 ** digits) - 1
        span = upper_bound - lower_bound + 1

        bit_length = span.bit_length() + 8
        raw_bits = self.next_bits(bit_length)
        return lower_bound + (raw_bits % span)
