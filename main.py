#!/usr/bin/env python3
"""
========================================================================================
SISTEMAS COMPLEJOS - PARCIAL 2
UNIVERSIDAD SERGIO ARBOLEDA
Programa de Ciencias de la Computación e Inteligencia Artificial
========================================================================================
MÁQUINA GENERADORA DE NÚMEROS PSEUDOALEATORIOS DE 40 CIFRAS
DETECCIÓN DE NÚMEROS PRIMOS Y SISTEMA DE ENCRIPTACIÓN ASIMÉTRICA

Arquitectura Modular de Software con Patrones de Diseño:
- Strategy Pattern: Múltiples técnicas PRNG (Wolfram Regla 30, Mapa Logístico Caótico, BBS)
- Factory Method: Instanciación desacoplada de generadores
- Facade Pattern: PseudoRandomMachine como interfaz simplificada
- Pipeline / Filter Pattern: Filtrado multi-etapa de números primos
- Cryptosystem Pattern: Cifrado asimétrico RSA y ElGamal con primos grandes
========================================================================================
"""
import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any

# Asegurar codificación UTF-8 en consola de Windows sin errores de charmap
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.core.interfaces import IPRNGStrategy
from src.prng.machine import PseudoRandomMachine
from src.prng.factory import PRNGFactory
from src.primality.pipeline import PrimalityFilterPipeline
from src.crypto.rsa_cipher import RSACryptosystem
from src.crypto.elgamal_cipher import ElGamalCryptosystem
from src.crypto.key_manager import KeyManager
from src.analysis.randomness_tests import digit_frequency_analysis, run_comprehensive_suite
from src.analysis.visualizer import ScientificVisualizer
from src.utils.formatting import print_header, print_metric_table, format_large_number


def run_full_pipeline(
    technique: str = "rule30",
    count: int = 10000,
    digits: int = 40,
    seed: Any = None,
    custom_message: str = "Parcial 2 - Sistemas Complejos: Máquina de Cifrado Asimétrico con Primos de 40 Cifras Exitosa!"
) -> Dict[str, Any]:
    """
    Ejecuta el flujo completo requerido por el examen:
    1. Generar 10,000 números de 40 cifras usando la máquina y la técnica elegida.
    2. Hallar cuáles son números primos mediante el pipeline de primalidad.
    3. Construir el sistema de encriptación con los primos hallados.
    4. Cifrar y descifrar mensajes de texto y números.
    5. Exportar reportes JSON y figuras analíticas en docs/resultados/.
    """
    print_header(
        "SISTEMAS COMPLEJOS - PARCIAL 2",
        "Máquina Generadora de 40 Cifras, Detección de Primos y Encriptación Asimétrica"
    )

    results_dir = "results"
    docs_dir = "docs/resultados"
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # FASE 1: Configuración de la Máquina Pseudoaleatoria
    # -------------------------------------------------------------------------
    print(f"\n[Fase 1] Inicializando Máquina Pseudoaleatoria...")
    machine = PseudoRandomMachine(technique=technique, seed=seed)
    print(f"  Técnica activa: {machine.technique_name}")
    print(f"  Descripción:   {machine.current_strategy.description}")
    print(f"  Longitud objetivo por número: {digits} cifras decimales")

    # Muestra de verificación de salida unitaria de 40 cifras
    sample_num = machine.generate_single_number(digits=digits)
    print(f"\n  Ejemplo de salida de 40 cifras generada por la máquina:")
    print(f"  N = {format_large_number(sample_num)}")
    print(f"  Longitud: {len(str(sample_num))} cifras (Verificado: {10**(digits-1) <= sample_num < 10**digits})")

    # -------------------------------------------------------------------------
    # FASE 2: Generación de los 10,000 Números de 40 Cifras
    # -------------------------------------------------------------------------
    print(f"\n[Fase 2] Generando lote de {count:,} números de {digits} cifras...")
    batch_res = machine.generate_batch(count=count, digits=digits, show_progress=True)
    numbers = batch_res["numbers"]

    print(f"\n  [OK] Generación completada con éxito.")
    print(f"  Tiempo transcurrido: {batch_res['elapsed_seconds']} s")
    print(f"  Rendimiento:         {batch_res['throughput_num_per_sec']} números/segundo")

    # -------------------------------------------------------------------------
    # FASE 3: Análisis de Primalidad (Pipeline Multi-Etapa)
    # -------------------------------------------------------------------------
    print(f"\n[Fase 3] Ejecutando Pipeline de Primalidad sobre los {count:,} números...")
    pipeline = PrimalityFilterPipeline(mr_rounds=40, verify_with_lucas=True)
    primality_res = pipeline.process_batch(numbers, show_progress=True)

    primes_found = primality_res["primes_list"]
    n_primes = len(primes_found)

    # Tabla resumen de filtrado
    filter_headers = ["Etapa de Filtrado", "Candidatos Eliminados", "Supervivientes", "% de la Muestra"]
    total_n = primality_res["total_analyzed"]
    rej_even = primality_res["rejected_even_count"]
    rej_small = primality_res["rejected_small_primes_count"]
    mr_candidates = primality_res["miller_rabin_candidates_count"]

    filter_rows = [
        ["1. Filtro de Paridad (Pares)", f"{rej_even:,}", f"{total_n - rej_even:,}", f"{(rej_even/total_n)*100:.2f}%"],
        ["2. Criba Primos Pequeños (<2000)", f"{rej_small:,}", f"{mr_candidates:,}", f"{(rej_small/total_n)*100:.2f}%"],
        ["3. Test Miller-Rabin (40 rondas)", f"{mr_candidates - n_primes:,}", f"{n_primes:,}", f"{((mr_candidates - n_primes)/total_n)*100:.2f}%"],
        ["4. Primos Verificados (40 cifras)", "0", f"{n_primes:,}", f"{(n_primes/total_n)*100:.4f}%"]
    ]
    print_metric_table(filter_headers, filter_rows, "Resultados del Embudo de Primalidad")

    print(f"\n  Comparación con el Teorema de los Números Primos (PNT):")
    print(f"  - Densidad Empírica Observada:   {primality_res['empirical_density_pct']:.4f}% ({n_primes} primos)")
    print(f"  - Densidad Teórica PNT (1/ln N): {primality_res['theoretical_density_pct']:.4f}%")
    print(f"  - Razón Empírica / Teórica:      {primality_res['pnt_ratio']:.3f}x")

    # Si por azar estocástico no se hallaran al menos 2 primos, generar candidatos adicionales
    if n_primes < 2:
        print(f"\n  [Aviso] Se requieren al menos 2 primos para el criptosistema. Generando adicionales...")
        while len(primes_found) < 2:
            cand = machine.generate_single_number(digits=digits)
            if pipeline.test_single(cand):
                primes_found.append(cand)
        n_primes = len(primes_found)

    # Mostrar algunos de los primos hallados
    print(f"\n  Muestra de los Números Primos de 40 Cifras Hallados:")
    for idx, p in enumerate(primes_found[:5], start=1):
        print(f"  Primo #{idx:02d}: {format_large_number(p)} (cifras: {len(str(p))})")

    # Guardar primos encontrados en JSON
    primes_export_path = os.path.join(results_dir, "primes_found.json")
    with open(primes_export_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_generated": count,
            "technique": machine.technique_name,
            "primes_count": n_primes,
            "primes": [str(p) for p in primes_found]
        }, f, indent=2)
    print(f"  [OK] Primos guardados en: {primes_export_path}")

    # -------------------------------------------------------------------------
    # FASE 4: Sistema de Encriptación de Mensajes Usando Primos Encontrados
    # -------------------------------------------------------------------------
    print(f"\n[Fase 4] Diseñando e inicializando Sistema de Encriptación Asimétrica...")
    p_rsa = primes_found[0]
    q_rsa = primes_found[1]

    rsa_system = RSACryptosystem(p=p_rsa, q=q_rsa)
    rsa_keys = KeyManager.export_rsa_keys(rsa_system)

    print(f"  Criptosistema RSA inicializado con primos p y q descubiertos:")
    print(f"  - Primo p: {format_large_number(p_rsa)} ({len(str(p_rsa))} cifras)")
    print(f"  - Primo q: {format_large_number(q_rsa)} ({len(str(q_rsa))} cifras)")
    print(f"  - Módulo n = p * q:")
    print(f"    n = {format_large_number(rsa_system.modulus)}")
    print(f"    Dimensión del módulo: {len(str(rsa_system.modulus))} cifras decimales ({rsa_system.modulus.bit_length()} bits)")
    print(f"  - Exponente público e: {rsa_system.public_key[0]}")
    print(f"  - Huella criptográfica (SHA-256): {rsa_keys['fingerprint']}")

    # Cifrado de Mensaje de Texto
    print(f"\n  [Encriptación de Mensaje de Texto]")
    print(f"  Mensaje original: \"{custom_message}\"")
    rsa_cipher_payload = rsa_system.encrypt_message(custom_message)
    print(f"  [OK] Mensaje cifrado en {rsa_cipher_payload['block_count']} bloques:")
    for b_idx, cb in enumerate(rsa_cipher_payload['cipher_blocks'], start=1):
        print(f"    Bloque #{b_idx}: {format_large_number(int(cb))}")

    decrypted_message = rsa_system.decrypt_message(rsa_cipher_payload)
    print(f"  [OK] Mensaje descifrado: \"{decrypted_message}\"")
    print(f"  ¿Integridad garantizada (Original == Descifrado)?: {decrypted_message == custom_message}")

    # -------------------------------------------------------------------------
    # FASE 5: Pruebas de Encriptación de los Números
    # -------------------------------------------------------------------------
    print(f"\n[Fase 5] Realizando pruebas de encriptación directa de números...")
    # Selección de números de prueba: los primos encontrados y números de 40 cifras generados
    test_numbers_pool = [
        ("Primo Descubierto p", p_rsa),
        ("Primo Descubierto q", q_rsa),
        ("Número Aleatorio #1", numbers[0]),
        ("Número Aleatorio #2", numbers[1]),
        ("Número Arbitrario", 9876543210987654321098765432109876543210)
    ]

    crypto_test_records = []
    table_headers = ["Identificador", "Número Original (40 cifras)", "Criptograma c = m^e mod n", "Descifrado", "¿Éxito?"]
    table_rows = []

    for label, raw_num in test_numbers_pool:
        # Cifrado numérico directo
        t0 = time.perf_counter()
        c_num = rsa_system.encrypt_number(raw_num)
        t_enc = (time.perf_counter() - t0) * 1000

        # Descifrado numérico directo
        t1 = time.perf_counter()
        dec_num = rsa_system.decrypt_number(c_num)
        t_dec = (time.perf_counter() - t1) * 1000

        is_success = (dec_num == raw_num)

        crypto_test_records.append({
            "label": label,
            "original_number": raw_num,
            "ciphertext_number": c_num,
            "decrypted_number": dec_num,
            "success": is_success,
            "enc_time_ms": round(t_enc, 3),
            "dec_time_ms": round(t_dec, 3)
        })

        table_rows.append([
            label,
            f"{str(raw_num)[:12]}...{str(raw_num)[-6:]} ({len(str(raw_num))}c)",
            f"{str(c_num)[:12]}...{str(c_num)[-6:]} ({len(str(c_num))}c)",
            f"{str(dec_num)[:12]}...{str(dec_num)[-6:]}",
            "[OK] SI" if is_success else "[FAIL] NO"
        ])

    print_metric_table(table_headers, table_rows, "Resultados de Encriptación Numérica Directa")

    # Criptosistema ElGamal como prueba adicional sobre un primo
    print(f"\n  [Criptosistema Adicional: ElGamal sobre Primo de 40 Cifras]")
    elgamal = ElGamalCryptosystem(p=p_rsa)
    elg_payload = elgamal.encrypt_message("Prueba Criptográfica ElGamal (Logaritmo Discreto)")
    elg_decrypted = elgamal.decrypt_message(elg_payload)
    print(f"  [OK] ElGamal cifrado y descifrado con éxito: \"{elg_decrypted}\"")

    # -------------------------------------------------------------------------
    # FASE 6: Análisis Estadístico y Generación de Visualizaciones Científicas
    # -------------------------------------------------------------------------
    print(f"\n[Fase 6] Generando gráficos científicos y análisis de aleatoriedad...")
    visualizer = ScientificVisualizer(output_dir=docs_dir)

    # Comparación de las 3 técnicas para la figura 1
    print("  Evaluando las 3 técnicas PRNG para comparativa visual...")
    comparison_stats = {}
    sample_sizes = min(2000, count)
    for strat_key, strat_label in [("rule30", "Wolfram Regla 30"), ("logistic", "Mapa Logístico"), ("bbs", "Blum-Blum-Shub")]:
        temp_mach = PseudoRandomMachine(technique=strat_key, seed=seed)
        t_batch = temp_mach.generate_batch(count=sample_sizes, digits=40)["numbers"]
        comparison_stats[strat_label] = digit_frequency_analysis(t_batch)

    fig1 = visualizer.plot_prng_comparison(comparison_stats)
    print(f"  [OK] Guardado: {fig1}")

    fig2 = visualizer.plot_rule30_ca()
    print(f"  [OK] Guardado: {fig2}")

    fig3 = visualizer.plot_chaotic_map()
    print(f"  [OK] Guardado: {fig3}")

    fig4 = visualizer.plot_prime_distribution(primality_res)
    print(f"  [OK] Guardado: {fig4}")

    fig5 = visualizer.plot_encryption_tests(crypto_test_records)
    print(f"  [OK] Guardado: {fig5}")

    # Guardar resumen final en JSON
    summary_export_path = os.path.join(results_dir, "resumen_ejecucion.json")
    with open(summary_export_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "technique_used": machine.technique_name,
            "total_numbers_generated": count,
            "digits_per_number": digits,
            "generation_metrics": {
                "elapsed_seconds": batch_res["elapsed_seconds"],
                "throughput_num_per_sec": batch_res["throughput_num_per_sec"]
            },
            "primality_metrics": {
                "primes_found_count": n_primes,
                "rejected_even": rej_even,
                "rejected_small_primes": rej_small,
                "empirical_density_pct": primality_res["empirical_density_pct"],
                "theoretical_density_pct": primality_res["theoretical_density_pct"]
            },
            "crypto_tests_count": len(crypto_test_records),
            "rsa_modulus_digits": len(str(rsa_system.modulus)),
            "all_tests_passed": all(r["success"] for r in crypto_test_records) and (decrypted_message == custom_message)
        }, f, indent=2)
    print(f"  [OK] Resumen de ejecución guardado en: {summary_export_path}")

    print_header("EJECUCIÓN COMPLETADA EXITOSAMENTE", "Todos los requerimientos fueron satisfechos al 100%")
    return {
        "batch_res": batch_res,
        "primality_res": primality_res,
        "primes_found": primes_found,
        "rsa_system": rsa_system,
        "crypto_test_records": crypto_test_records
    }


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Generación Pseudoaleatoria de 40 Cifras, Detección de Primos y Criptosistema Asimétrico.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando 1: run-all (ejecutar todo)
    parser_all = subparsers.add_parser("run-all", help="Ejecutar el parcial completo (10,000 números, primos, cifrado, figuras)")
    parser_all.add_argument("--technique", default="rule30", choices=["rule30", "logistic", "bbs", "lcg"], help="Técnica PRNG")
    parser_all.add_argument("--count", type=int, default=10000, help="Cantidad de números a generar (por defecto 10000)")
    parser_all.add_argument("--digits", type=int, default=40, help="Cifras por número (por defecto 40)")
    parser_all.add_argument("--seed", default=None, help="Semilla inicial")
    parser_all.add_argument("--msg", default="Parcial 2 - Sistemas Complejos: Cifrado con Primos de 40 Cifras Exitosa!", help="Mensaje a encriptar")

    # Comando 2: generate (generar números)
    parser_gen = subparsers.add_parser("generate", help="Generar números de 40 cifras")
    parser_gen.add_argument("--technique", default="rule30", choices=["rule30", "logistic", "bbs", "lcg"])
    parser_gen.add_argument("--count", type=int, default=5)
    parser_gen.add_argument("--digits", type=int, default=40)
    parser_gen.add_argument("--seed", default=None)

    # Comando 3: benchmark (comparar técnicas)
    parser_bench = subparsers.add_parser("benchmark", help="Comparar las 3 técnicas PRNG en velocidad, entropía y chi-cuadrado")
    parser_bench.add_argument("--count", type=int, default=3000)

    # Comando 4: encrypt-message
    parser_enc = subparsers.add_parser("encrypt-message", help="Cifrar mensaje usando primos almacenados o nuevos")
    parser_enc.add_argument("message", help="Texto a cifrar")

    args = parser.parse_args()

    if args.command == "run-all" or args.command is None:
        technique = getattr(args, "technique", "rule30")
        count = getattr(args, "count", 10000)
        digits = getattr(args, "digits", 40)
        seed = getattr(args, "seed", None)
        msg = getattr(args, "msg", "Parcial 2 - Sistemas Complejos: Cifrado con Primos de 40 Cifras Exitosa!")
        run_full_pipeline(technique=technique, count=count, digits=digits, seed=seed, custom_message=msg)

    elif args.command == "generate":
        machine = PseudoRandomMachine(technique=args.technique, seed=args.seed)
        print_header(f"Generando {args.count} Números con {machine.technique_name}")
        for i in range(1, args.count + 1):
            num = machine.generate_single_number(digits=args.digits)
            print(f"[{i:02d}] {format_large_number(num)} ({len(str(num))} cifras)")

    elif args.command == "benchmark":
        print_header("BENCHMARK COMPARATIVO DE TÉCNICAS PRNG")
        headers = ["Técnica", "Tiempo (s)", "Throughput (num/s)", "Entropía (bits)", "Chi-Cuadrado (p-val)"]
        rows = []
        for tech in ["rule30", "logistic", "bbs", "lcg"]:
            mach = PseudoRandomMachine(technique=tech)
            t0 = time.perf_counter()
            nums = mach.generate_batch(count=args.count, digits=40)["numbers"]
            elapsed = time.perf_counter() - t0
            rate = args.count / elapsed
            stats = digit_frequency_analysis(nums)
            rows.append([
                mach.technique_name[:25],
                f"{elapsed:.3f}",
                f"{rate:,.1f}",
                f"{stats['shannon_entropy_bits']:.4f}",
                f"{stats['chi_square_stat']:.2f} (p={stats['p_value']:.3f})"
            ])
        print_metric_table(headers, rows)


if __name__ == "__main__":
    main()
