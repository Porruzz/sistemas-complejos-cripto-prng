"""
Máquina Generadora de Números Pseudoaleatorios de 40 Cifras.
Patrón Facade / Engine: Orquesta la configuración, selección de técnicas y generación masiva.
"""
import time
from typing import List, Dict, Any, Optional, Callable, Union
from src.core.interfaces import IPRNGStrategy
from src.core.exceptions import PRNGConfigError
from .factory import PRNGFactory


class PseudoRandomMachine:
    """
    Máquina para generar salidas de números pseudoaleatorios de 40 cifras (o longitud arbitraria).
    
    Integra múltiples técnicas de generación (Autómata Regla 30, Mapa Caótico Dinámico,
    Blum-Blum-Shub, LCG) mediante el Patrón Strategy y ofrece una interfaz unificada (Facade)
    para parametrización, generación individual y generación en lotes masivos (10,000 números).
    """

    DEFAULT_DIGITS = 40

    def __init__(
        self,
        technique: Union[str, IPRNGStrategy] = "rule30",
        seed: Optional[Any] = None,
        **extra_params: Any
    ):
        self._strategy: IPRNGStrategy = None  # type: ignore
        self.set_strategy(technique, seed=seed, **extra_params)

    @property
    def current_strategy(self) -> IPRNGStrategy:
        """Estrategia PRNG actualmente activa en la máquina."""
        return self._strategy

    @property
    def technique_name(self) -> str:
        """Nombre formal de la técnica activa."""
        return self._strategy.name

    def set_strategy(
        self,
        technique: Union[str, IPRNGStrategy],
        seed: Optional[Any] = None,
        **extra_params: Any
    ) -> None:
        """
        Cambia o reconfigura la estrategia generadora de la máquina.
        
        Args:
            technique: Nombre de la técnica ("rule30", "logistic", "bbs") o instancia de IPRNGStrategy.
            seed: Semilla inicial (opcional).
            **extra_params: Parámetros específicos de la técnica.
        """
        if isinstance(technique, IPRNGStrategy):
            self._strategy = technique
            if seed is not None or extra_params:
                self._strategy.configure(seed=seed, **extra_params)
        elif isinstance(technique, str):
            params = dict(extra_params)
            if seed is not None:
                params["seed"] = seed
            self._strategy = PRNGFactory.create(technique, **params)
        else:
            raise PRNGConfigError(f"Tipo de técnica no soportado: {type(technique)}")

    def generate_single_number(self, digits: int = DEFAULT_DIGITS) -> int:
        """
        Genera una única salida de un número pseudoaleatorio de `digits` cifras.
        
        Garantiza contractualmente que:
        1. El número es un entero positivo.
        2. len(str(N)) == digits.
        3. 10^(digits-1) <= N <= 10^digits - 1.
        """
        num = self._strategy.generate_number(digits=digits)
        # Verificación estricta de invariante
        str_repr = str(num)
        if len(str_repr) != digits:
            raise RuntimeError(
                f"Invariante violada: Se esperaba número de {digits} cifras, obtenido de {len(str_repr)} cifras: {num}"
            )
        return num

    def generate_batch(
        self,
        count: int = 10000,
        digits: int = DEFAULT_DIGITS,
        show_progress: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Genera un lote masivo de `count` números pseudoaleatorios de `digits` cifras.
        
        Args:
            count: Cantidad total de números a generar (por defecto 10,000).
            digits: Cifras de cada número (por defecto 40).
            show_progress: Si es True, imprime progreso en consola cada 1,000 números.
            progress_callback: Función opcional callback(generados, total).
            
        Returns:
            Dict con métricas de generación y lista completa de números.
        """
        if count <= 0:
            raise ValueError("La cantidad de números a generar debe ser mayor que cero.")

        t_start = time.perf_counter()
        numbers: List[int] = []

        step_checkpoint = max(1, count // 10)

        for i in range(1, count + 1):
            num = self.generate_single_number(digits=digits)
            numbers.append(num)

            if progress_callback:
                progress_callback(i, count)

            if show_progress and (i % step_checkpoint == 0 or i == count):
                elapsed_cur = time.perf_counter() - t_start
                rate = i / elapsed_cur if elapsed_cur > 0 else 0
                pct = (i / count) * 100
                print(f"  [PRNG Machine] Progreso: {i:,}/{count:,} ({pct:5.1f}%) | "
                      f"Tasa: {rate:8.1f} num/s | Transcurrido: {elapsed_cur:.2f}s")

        t_total = time.perf_counter() - t_start
        throughput = count / t_total if t_total > 0 else float("inf")

        return {
            "technique": self.technique_name,
            "count": count,
            "digits": digits,
            "elapsed_seconds": round(t_total, 4),
            "throughput_num_per_sec": round(throughput, 2),
            "numbers": numbers
        }
