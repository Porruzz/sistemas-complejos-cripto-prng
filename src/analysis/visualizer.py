"""
Módulo de Visualización Científica de Alta Calidad (Matplotlib).
Genera figuras científicas en docs/resultados/ que documentan:
1. Comparación de calidad estadística de las 3 técnicas PRNG (Chi-cuadrado y entropía).
2. Patrón espacio-temporal caótico del Autómata Celular Regla 30 de Wolfram.
3. Bifurcación y sensibilidad extrema a condiciones iniciales del Mapa Logístico.
4. Embudo de filtrado de primalidad, distribución de primos de 40 cifras y comparación con el PNT.
5. Efecto avalancha y verificación de encriptación numérica asimétrica.
"""
import os
import math
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional

# Configurar estilo visual limpio y profesional
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.titlesize": 13,
    "figure.autolayout": True
})


class ScientificVisualizer:
    """Generador de gráficos analíticos para el reporte de Sistemas Complejos."""

    def __init__(self, output_dir: str = "docs/resultados"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_prng_comparison(
        self,
        strategy_data: Dict[str, Dict[str, Any]],
        filename: str = "01_comparacion_prng.png"
    ) -> str:
        """
        Genera gráfico comparativo de frecuencias de dígitos (0-9) y métricas de entropía
        para las técnicas de generación pseudoaleatoria.
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
        digits = np.arange(10)
        expected_pct = 10.0  # 10% por dígito

        colors = ["#2b5c8f", "#d95f02", "#7570b3"]

        for idx, (strat_name, data) in enumerate(strategy_data.items()):
            if idx >= 3:
                break
            ax = axes[idx]
            pcts = data.get("percentages", [10]*10)
            chi_sq = data.get("chi_square_stat", 0.0)
            p_val = data.get("p_value", 0.0)
            entropy = data.get("shannon_entropy_bits", 0.0)

            bars = ax.bar(digits, pcts, color=colors[idx % len(colors)], alpha=0.85, edgecolor="black")
            ax.axhline(expected_pct, color="red", linestyle="--", linewidth=1.5, label="Uniforme teórico (10%)")

            ax.set_title(f"{strat_name}\n"
                         f"$\\chi^2 = {chi_sq:.2f}$ (p={p_val:.3f}) | H={entropy:.4f} bits",
                         fontsize=11)
            ax.set_xlabel("Dígito decimal")
            ax.set_xticks(digits)
            if idx == 0:
                ax.set_ylabel("Frecuencia observada (%)")
            ax.set_ylim(8.0, 12.0)
            ax.legend(loc="upper right", frameon=True)

        fig.suptitle("Comparación de Distribución de Dígitos y Entropía en Técnicas PRNG (40 Cifras)",
                     fontsize=14, fontweight="bold", y=1.02)
        out_path = os.path.join(self.output_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_rule30_ca(
        self,
        steps: int = 120,
        width: int = 241,
        filename: str = "02_automata_regla30.png"
    ) -> str:
        """
        Genera visualización del cono de luz y dinámica caótica espacio-temporal
        del Autómata Celular Regla 30 de Stephen Wolfram.
        """
        grid = np.zeros((steps, width), dtype=np.uint8)
        center = width // 2
        grid[0, center] = 1

        mask = (1 << width) - 1
        state = 1 << center

        # Evolucionar autómata
        for t in range(1, steps):
            left = ((state << 1) | (state >> (width - 1))) & mask
            right = ((state >> 1) | (state << (width - 1))) & mask
            state = (left ^ (state | right)) & mask
            for x in range(width):
                grid[t, x] = (state >> x) & 1

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={'width_ratios': [2, 1]})

        ax1.imshow(grid, cmap="binary", interpolation="nearest", aspect="auto")
        ax1.axvline(center, color="red", linestyle=":", linewidth=1.2, label="Columna de muestreo PRNG")
        ax1.set_title("Evolución Espacio-Temporal: Wolfram Regla 30 (Clase 3: Caos)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Posición espacial de la celda (i)")
        ax1.set_ylabel("Paso de tiempo discreto (t)")
        ax1.legend(loc="upper right")

        # Gráfico del flujo temporal del centro
        center_series = grid[:, center]
        ax2.step(np.arange(steps), center_series, where="post", color="#2b5c8f", linewidth=1.2)
        ax2.set_title("Flujo de Bits de la Celda Central", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Paso de tiempo (t)")
        ax2.set_ylabel("Estado binario c_center(t)")
        ax2.set_yticks([0, 1])
        ax2.grid(True, linestyle="--", alpha=0.6)

        fig.suptitle("Técnica 1: Autómata Celular 1D (Stephen Wolfram, 1983) como Generador Criptográfico",
                     fontsize=13, fontweight="bold")
        out_path = os.path.join(self.output_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_chaotic_map(
        self,
        filename: str = "03_mapa_logistico_caos.png"
    ) -> str:
        """
        Genera el diagrama de bifurcación del mapa logístico y la divergencia exponencial
        de dos trayectorias con perturbación microscópica (Efecto Mariposa).
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 1. Diagrama de bifurcación
        r_values = np.linspace(2.8, 4.0, 600)
        iterations = 300
        last_points = 80
        x_plot, r_plot = [], []

        for r in r_values:
            x = 0.5
            for _ in range(iterations - last_points):
                x = r * x * (1 - x)
            for _ in range(last_points):
                x = r * x * (1 - x)
                r_plot.append(r)
                x_plot.append(x)

        ax1.scatter(r_plot, x_plot, s=0.08, c="#2c3e50", alpha=0.4)
        ax1.axvline(3.5699, color="darkred", linestyle="--", label="Acumulación de Feigenbaum (Caos)")
        ax1.axvline(4.0, color="crimson", linestyle=":", label="Régimen PRNG r=4.0 (Caos completo)")
        ax1.set_title("Diagrama de Bifurcación: x_{n+1} = r x_n (1 - x_n)", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Parámetro de control r")
        ax1.set_ylabel("Atractor assintótico x*")
        ax1.legend(loc="upper left")

        # 2. Sensibilidad a condiciones iniciales (Efecto Mariposa)
        n_steps = 55
        t = np.arange(n_steps)
        r_chaos = 4.0
        x1_traj, x2_traj = [0.5], [0.5000000001]
        for _ in range(n_steps - 1):
            x1_traj.append(r_chaos * x1_traj[-1] * (1 - x1_traj[-1]))
            x2_traj.append(r_chaos * x2_traj[-1] * (1 - x2_traj[-1]))

        ax2.plot(t, x1_traj, "b-o", markersize=3, label="Trayectoria A: x_0 = 0.5000000000", alpha=0.8)
        ax2.plot(t, x2_traj, "r--s", markersize=3, label="Trayectoria B: x_0 = 0.5000000001", alpha=0.8)
        ax2.set_title("Sensibilidad a Condiciones Iniciales (Divergencia Lyapunov)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Paso discreto (n)")
        ax2.set_ylabel("Estado dinámico x_n")
        ax2.legend(loc="upper right")

        fig.suptitle("Técnica 2: Caos Determinista no Lineal como Motor de Generación Pseudoaleatoria",
                     fontsize=13, fontweight="bold")
        out_path = os.path.join(self.output_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_prime_distribution(
        self,
        pipeline_stats: Dict[str, Any],
        filename: str = "04_distribucion_primos.png"
    ) -> str:
        """
        Visualiza el embudo de filtrado de los 10,000 números y la densidad de primos frente al PNT.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 1. Embudo de filtrado (Funnel)
        stages = ["Muestra total", "Paridad (Impares)", "Pasa Criba <2000", "Primos Verificados"]
        total = pipeline_stats.get("total_analyzed", 10000)
        rejected_even = pipeline_stats.get("rejected_even_count", total // 2)
        survived_even = total - rejected_even
        survived_sieve = pipeline_stats.get("miller_rabin_candidates_count", 0)
        primes_count = pipeline_stats.get("primes_found_count", 0)

        counts = [total, survived_even, survived_sieve, primes_count]
        colors = ["#34495e", "#2980b9", "#f39c12", "#27ae60"]

        bars = ax1.bar(stages, counts, color=colors, edgecolor="black", alpha=0.85)
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + max(total*0.01, 50),
                     f"{height:,}", ha="center", va="bottom", fontweight="bold", fontsize=9)

        ax1.set_title("Embudo de Filtrado Masivo (10,000 Candidatos de 40 Cifras)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Cantidad de candidatos supervivientes")
        ax1.set_ylim(0, total * 1.15)

        # 2. Densidad observada vs PNT
        categories = ["Densidad Empírica", "Teorema Números Primos (PNT)"]
        emp_pct = pipeline_stats.get("empirical_density_pct", 0.0)
        theo_pct = pipeline_stats.get("theoretical_density_pct", 1.0857)

        density_bars = ax2.bar(categories, [emp_pct, theo_pct], color=["#27ae60", "#8e44ad"], edgecolor="black", width=0.5)
        for bar in density_bars:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., h + 0.05,
                     f"{h:.4f}%", ha="center", va="bottom", fontweight="bold", fontsize=10)

        ax2.set_title("Densidad de Primos de 40 Cifras: Empírica vs Teórica", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Porcentaje de Primos en la Muestra (%)")
        ax2.set_ylim(0, max(emp_pct, theo_pct) * 1.35)

        fig.suptitle("Pipeline de Primalidad: Filtrado de 10,000 Números de 40 Cifras",
                     fontsize=13, fontweight="bold")
        out_path = os.path.join(self.output_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_encryption_tests(
        self,
        test_samples: List[Dict[str, Any]],
        filename: str = "05_pruebas_encriptacion.png"
    ) -> str:
        """
        Visualiza pruebas de encriptación numérica: relación biunívoca,
        transformación del valor plano al criptograma y dispersión modular.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Longitud en cifras de entradas y criptogramas
        sample_indices = np.arange(1, len(test_samples) + 1)
        plain_digits = [len(str(s["original_number"])) for s in test_samples]
        cipher_digits = [len(str(s["ciphertext_number"])) for s in test_samples]

        width = 0.35
        ax1.bar(sample_indices - width/2, plain_digits, width, label="Número Plano (m)", color="#3498db")
        ax1.bar(sample_indices + width/2, cipher_digits, width, label="Criptograma (c = m^e mod n)", color="#e74c3c")
        ax1.set_title("Dimensión Decimal: Número Original vs Criptograma RSA", fontsize=11, fontweight="bold")
        ax1.set_xlabel("Muestra de Prueba")
        ax1.set_ylabel("Cifras Decimales")
        ax1.set_xticks(sample_indices)
        ax1.set_ylim(0, max(cipher_digits) * 1.25)
        ax1.legend(loc="upper right")

        # Dispersión modular / Entropía de los bits cifrados
        # Representación de los primeros 100 bits de un criptograma vs número plano
        sample = test_samples[0]
        plain_bits = [int(b) for b in bin(sample["original_number"])[2:].zfill(260)[:100]]
        cipher_bits = [int(b) for b in bin(sample["ciphertext_number"])[2:].zfill(260)[:100]]

        ax2.step(range(100), plain_bits, label="Bits Plano (m)", color="#2980b9", alpha=0.7)
        ax2.step(range(100), cipher_bits, label="Bits Criptograma (c)", color="#c0392b", alpha=0.7)
        ax2.set_title("Dispersión Criptográfica (Mapeo no lineal mod n)", fontsize=11, fontweight="bold")
        ax2.set_xlabel("Índice de Bit")
        ax2.set_ylabel("Valor binario (0 o 1)")
        ax2.set_yticks([0, 1])
        ax2.legend(loc="upper right")

        fig.suptitle("Pruebas de Cifrado y Descifrado Asimétrico con Primos de 40 Cifras",
                     fontsize=13, fontweight="bold")
        out_path = os.path.join(self.output_dir, filename)
        fig.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return out_path
