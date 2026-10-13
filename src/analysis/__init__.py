"""Módulo de Análisis Estadístico y Visualización Científica."""
from .randomness_tests import digit_frequency_analysis, serial_autocorrelation_lag1, run_comprehensive_suite
from .visualizer import ScientificVisualizer

__all__ = [
    "digit_frequency_analysis",
    "serial_autocorrelation_lag1",
    "run_comprehensive_suite",
    "ScientificVisualizer"
]
