"""
Fábrica de Generadores Pseudoaleatorios (Patrón Factory Method / Abstract Factory).
Instancia y desacopla la creación de estrategias PRNG según configuración.
"""
from typing import Dict, Type, Any, Optional
from src.core.interfaces import IPRNGStrategy
from src.core.exceptions import PRNGConfigError
from .rule30_ca import WolframRule30Strategy
from .chaotic_map import ChaoticLogisticStrategy
from .blum_blum_shub import BlumBlumShubStrategy
from .lcg_strategy import LCGStrategy


class PRNGFactory:
    """Fábrica para instanciación desacoplada de generadores pseudoaleatorios."""

    _STRATEGIES: Dict[str, Type[IPRNGStrategy]] = {
        "rule30": WolframRule30Strategy,
        "wolfram": WolframRule30Strategy,
        "cellular_automaton": WolframRule30Strategy,
        "logistic": ChaoticLogisticStrategy,
        "chaos": ChaoticLogisticStrategy,
        "chaotic_map": ChaoticLogisticStrategy,
        "bbs": BlumBlumShubStrategy,
        "blum": BlumBlumShubStrategy,
        "blum_blum_shub": BlumBlumShubStrategy,
        "lcg": LCGStrategy
    }

    @classmethod
    def register_strategy(cls, alias: str, strategy_cls: Type[IPRNGStrategy]) -> None:
        """Permite registrar nuevas estrategias dinámicamente en tiempo de ejecución (Principio Abierto/Cerrado)."""
        cls._STRATEGIES[alias.lower().strip()] = strategy_cls

    @classmethod
    def get_available_strategies(cls) -> Dict[str, str]:
        """Retorna un diccionario de alias únicos y nombres de las técnicas registradas."""
        seen = set()
        result = {}
        for alias, strat_cls in cls._STRATEGIES.items():
            if strat_cls not in seen:
                seen.add(strat_cls)
                result[alias] = strat_cls.__name__
        return result

    @classmethod
    def create(cls, technique: str = "rule30", **params: Any) -> IPRNGStrategy:
        """
        Crea e inicializa una estrategia PRNG según el alias proporcionado.
        
        Args:
            technique: Nombre o alias de la técnica ("rule30", "logistic", "bbs", "lcg").
            **params: Parámetros específicos para la estrategia (seed, etc.).
        
        Returns:
            Instancia configurada de IPRNGStrategy.
        """
        key = technique.lower().strip()
        if key not in cls._STRATEGIES:
            available = ", ".join(sorted(set(cls._STRATEGIES.keys())))
            raise PRNGConfigError(
                f"Técnica desconocida '{technique}'. Estrategias disponibles: {available}"
            )

        strategy_cls = cls._STRATEGIES[key]
        instance = strategy_cls(**params)
        return instance
