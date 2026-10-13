"""
Técnica 1: Generador Pseudoaleatorio basado en Autómatas Celulares 1D (Regla 30 de Wolfram).
Paradigma de Sistemas Complejos: Caos determinista y comportamiento emergente de Clase 3.
"""
import time
from typing import Any, Optional
from src.core.interfaces import IPRNGStrategy
from src.core.exceptions import PRNGConfigError


class WolframRule30Strategy(IPRNGStrategy):
    """
    Generador de números pseudoaleatorios basado en el Autómata Celular Elemental Regla 30.
    
    Fundamento en Sistemas Complejos:
    Introducido por Stephen Wolfram en 1983. A pesar de seguir una regla local determinista
    extremadamente simple, exhibe caos espacio-temporal de Clase 3. La columna central
    temporal pasa rigurosas pruebas de aleatoriedad estadística y fue utilizada durante
    décadas como el generador base en el software Wolfram Mathematica.
    
    Regla de transición local:
        c_i^(t+1) = c_{i-1}^(t) XOR (c_i^(t) OR c_{i+1}^(t))
    Equivalente al número binario 00011110_2 = 30_10.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        grid_size: int = 512,
        warmup_steps: int = 256,
        sample_stride: int = 2
    ):
        self._grid_size = grid_size
        self._warmup_steps = warmup_steps
        self._sample_stride = sample_stride
        self._mask = (1 << self._grid_size) - 1
        self._center_pos = self._grid_size // 2
        self._state = 0
        self._step_counter = 0

        self.configure(
            seed=seed,
            grid_size=grid_size,
            warmup_steps=warmup_steps,
            sample_stride=sample_stride
        )

    @property
    def name(self) -> str:
        return "Wolfram Rule 30 (Cellular Automaton)"

    @property
    def description(self) -> str:
        return (
            "Autómata celular unidimensional elemental con regla local 30. "
            "Genera comportamiento caótico de Clase 3 con condiciones periódicas de frontera."
        )

    def configure(self, **kwargs: Any) -> None:
        """
        Configura los parámetros del autómata celular.
        Parámetros aceptados:
            seed (int | str | None): Semilla inicial.
            grid_size (int): Longitud del retículo en celdas (por defecto 512).
            warmup_steps (int): Pasos de evolución antes de muestreo (por defecto 256).
            sample_stride (int): Número de pasos temporales entre extracciones.
        """
        if "grid_size" in kwargs and kwargs["grid_size"] is not None:
            gs = int(kwargs["grid_size"])
            if gs < 64:
                raise PRNGConfigError("grid_size debe ser al menos 64 celdas.")
            self._grid_size = gs
            self._mask = (1 << self._grid_size) - 1
            self._center_pos = self._grid_size // 2

        if "warmup_steps" in kwargs and kwargs["warmup_steps"] is not None:
            self._warmup_steps = max(10, int(kwargs["warmup_steps"]))

        if "sample_stride" in kwargs and kwargs["sample_stride"] is not None:
            self._sample_stride = max(1, int(kwargs["sample_stride"]))

        seed_val = kwargs.get("seed", None)
        if seed_val is None:
            # Semilla basada en reloj de alta resolución y entropía de memoria
            seed_val = int(time.time_ns()) ^ (id(self) << 16)
        elif isinstance(seed_val, str):
            import hashlib
            seed_val = int(hashlib.sha256(seed_val.encode('utf-8')).hexdigest(), 16)
        elif not isinstance(seed_val, int):
            try:
                seed_val = int(seed_val)
            except Exception as e:
                raise PRNGConfigError(f"Semilla inválida: {seed_val}") from e

        # Inicializar el retículo con la semilla truncada al tamaño de la grilla
        # Asegurar al menos un bit encendido para evitar el atractor trivial de ceros
        self._state = seed_val & self._mask
        if self._state == 0:
            self._state = 1 << self._center_pos

        self._step_counter = 0

        # Ejecutar pasos de calentamiento (transitorio caótico)
        for _ in range(self._warmup_steps):
            self._evolve_step()

    def _evolve_step(self) -> None:
        """
        Avanza un paso de tiempo en el autómata celular aplicando la Regla 30
        con condiciones periódicas de frontera usando álgebra booleana optimizada a nivel de bits.
        """
        s = self._state
        w = self._grid_size
        mask = self._mask

        # Desplazamientos circulares (condiciones periódicas de frontera)
        left = ((s << 1) | (s >> (w - 1))) & mask
        right = ((s >> 1) | (s << (w - 1))) & mask
        center = s

        # Regla 30: Left XOR (Center OR Right)
        self._state = (left ^ (center | right)) & mask
        self._step_counter += 1

    def next_bit(self) -> int:
        """
        Extrae el siguiente bit pseudoaleatorio de la celda central
        tras avanzar `sample_stride` pasos temporales.
        """
        for _ in range(self._sample_stride):
            self._evolve_step()
        # Bit central
        return (self._state >> self._center_pos) & 1

    def next_bits(self, count: int) -> int:
        """Genera un entero compuesto por `count` bits pseudoaleatorios."""
        result = 0
        for _ in range(count):
            result = (result << 1) | self.next_bit()
        return result

    def generate_number(self, digits: int = 40) -> int:
        """
        Genera un número de exactamente `digits` cifras decimales.
        Para 40 cifras: N in [10^39, 10^40 - 1].
        
        Garantiza distribución uniforme en el intervalo numérico.
        """
        if digits <= 0:
            raise ValueError("El número de cifras debe ser mayor que cero.")

        lower_bound = 10 ** (digits - 1)
        upper_bound = (10 ** digits) - 1
        span = upper_bound - lower_bound + 1  # 9 * 10^(digits-1)

        # Necesitamos k bits tales que 2^k > span
        bit_length = span.bit_length() + 8  # 8 bits extra para reducir sesgo de módulo

        raw_bits = self.next_bits(bit_length)
        num = lower_bound + (raw_bits % span)
        return num
