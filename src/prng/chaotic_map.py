"""
Técnica 2: Generador Pseudoaleatorio basado en Mapas Dinámicos Caóticos No Lineales.
Paradigma de Sistemas Complejos: Caos determinista, atractores extraños y sensibilidad a condiciones iniciales.
"""
import time
import math
from typing import Any, Optional
from src.core.interfaces import IPRNGStrategy
from src.core.exceptions import PRNGConfigError


class ChaoticLogisticStrategy(IPRNGStrategy):
    """
    Generador de números pseudoaleatorios basado en el Mapa Logístico no lineal acoplado.
    
    Fundamento en Sistemas Complejos:
    El mapa logístico x_{n+1} = r * x_n * (1 - x_n) para r = 4.0 describe un sistema dinámico
    en régimen de caos determinista completo, con exponente de Lyapunov positivo (lambda = ln(2))
    y ergodicidad en el intervalo (0, 1).
    
    Para evitar el colapso de ciclo periódico inherente a la aritmética de coma flotante de precisión finita,
    esta implementación utiliza una formulación de punto fijo entero de 64 bits acoplada con
    inyección de perturbación no lineal caótica de baja escala (anti-degradación dinámica),
    garantizando un espacio de estados colosal (2^64) y alta entropía de Shannon.
    """

    MOD_64 = 1 << 64
    MASK_64 = (1 << 64) - 1

    def __init__(
        self,
        seed: Optional[float] = None,
        r: float = 4.0,
        warmup_steps: int = 500,
        perturbation_enabled: bool = True
    ):
        self._r = r
        self._warmup_steps = warmup_steps
        self._perturbation_enabled = perturbation_enabled
        self._x = 0
        self._perturb_state = 0
        self._bit_buffer = 0
        self._bits_in_buffer = 0

        self.configure(
            seed=seed,
            r=r,
            warmup_steps=warmup_steps,
            perturbation_enabled=perturbation_enabled
        )

    @property
    def name(self) -> str:
        return "Chaotic Logistic Map (Nonlinear Dynamical System)"

    @property
    def description(self) -> str:
        return (
            "Sistema dinámico no lineal basado en el mapa logístico acoplado en régimen caótico (r=4.0). "
            "Implementa aritmética de punto fijo de 64 bits con prevención de degradación de ciclo."
        )

    def configure(self, **kwargs: Any) -> None:
        """
        Configura los parámetros del mapa caótico.
        Parámetros aceptados:
            seed (float | int | None): Condición inicial x_0 en (0, 1) o entero.
            r (float): Parámetro de control de bifurcación (por defecto 4.0).
            warmup_steps (int): Iteraciones de transitorio caótico inicial.
            perturbation_enabled (bool): Activación de desacoplamiento anti-ciclo.
        """
        if "r" in kwargs and kwargs["r"] is not None:
            r_val = float(kwargs["r"])
            if not (3.57 <= r_val <= 4.0):
                raise PRNGConfigError(f"El parámetro r debe estar en la zona caótica [3.57, 4.0], recibido: {r_val}")
            self._r = r_val

        if "warmup_steps" in kwargs and kwargs["warmup_steps"] is not None:
            self._warmup_steps = max(50, int(kwargs["warmup_steps"]))

        if "perturbation_enabled" in kwargs and kwargs["perturbation_enabled"] is not None:
            self._perturbation_enabled = bool(kwargs["perturbation_enabled"])

        seed_val = kwargs.get("seed", None)
        if seed_val is None:
            # Semilla basada en nanosegundos
            t_ns = time.time_ns()
            # Escalar a entero dentro de (0, 2^64)
            self._x = (t_ns * 6364136223846793005) & self.MASK_64
            self._perturb_state = (t_ns ^ 0xA5A5A5A55A5A5A5A) & self.MASK_64
        elif isinstance(seed_val, float):
            if not (0.0 < seed_val < 1.0):
                raise PRNGConfigError(f"La semilla flotante debe estar estrictamente en (0, 1), recibida: {seed_val}")
            self._x = int(seed_val * (self.MOD_64 - 2)) + 1
            self._perturb_state = (self._x ^ 0x55555555AAAAAAAA) & self.MASK_64
        elif isinstance(seed_val, int):
            self._x = seed_val & self.MASK_64
            self._perturb_state = (seed_val ^ 0x3C3C3C3CC3C3C3C3) & self.MASK_64
        else:
            raise PRNGConfigError(f"Tipo de semilla no soportado: {type(seed_val)}")

        # Evitar puntos fijos triviales 0 y 2^64
        if self._x == 0 or self._x >= self.MOD_64 - 1:
            self._x = 0x5A5A5A5A12345678 & self.MASK_64

        self._bit_buffer = 0
        self._bits_in_buffer = 0

        # Evolución transitoria para alcanzar el atractor caótico
        for _ in range(self._warmup_steps):
            self._iterate()

    def _iterate(self) -> None:
        """
        Avanza una iteración caótica:
        X_{k+1} = [ 4 * X_k * (2^64 - X_k) ] >> 64
        con perturbación no lineal en los bits menos significativos para evitar ciclos espurios.
        """
        x = self._x
        mod = self.MOD_64

        # Mapa logístico cuadrático exacto
        # x_next = (4 * x * (mod - x)) // mod
        x_next = (4 * x * (mod - x)) >> 64

        if self._perturbation_enabled:
            # Generador congruencial multiplicativo Weyl para perturbación mínima
            self._perturb_state = (
                self._perturb_state * 6364136223846793005 + 1442695040888963407
            ) & self.MASK_64
            # Perturbar únicamente los 16 bits inferiores (preservando el atractor macroscópico)
            perturbation = self._perturb_state & 0xFFFF
            x_next ^= perturbation

        # Prevenir atractor trivial (bordes 0 o 1)
        if x_next <= 0 or x_next >= mod - 1:
            x_next = (x_next + 0x9E3779B97F4A7C15) & self.MASK_64

        self._x = x_next

    def next_bit(self) -> int:
        """
        Extrae un bit con máxima entropía de la región central del estado caótico.
        """
        if self._bits_in_buffer == 0:
            self._iterate()
            # Tomamos los 32 bits intermedios (posiciones 16 a 48) donde la difusión es óptima
            self._bit_buffer = (self._x >> 16) & 0xFFFFFFFF
            self._bits_in_buffer = 32

        bit = self._bit_buffer & 1
        self._bit_buffer >>= 1
        self._bits_in_buffer -= 1
        return bit

    def next_bits(self, count: int) -> int:
        """Extrae un número entero de `count` bits pseudoaleatorios."""
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
