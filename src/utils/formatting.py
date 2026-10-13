"""
Utilidades de presentación en consola, formateo de números grandes y tablas.
"""
from typing import List, Dict, Any
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
except ImportError:
    CYAN = GREEN = YELLOW = RED = MAGENTA = RESET = BOLD = ""


def format_large_number(num: int, group_size: int = 10, sep: str = " ") -> str:
    """
    Formatea un número entero de gran tamaño separando dígitos en bloques.
    Ejemplo: para 40 cifras genera 4 bloques de 10 dígitos.
    """
    s = str(num)
    chunks = [s[i:i + group_size] for i in range(0, len(s), group_size)]
    return sep.join(chunks)


def print_header(title: str, subtitle: str = ""):
    """Imprime un encabezado estilizado en consola."""
    width = 78
    print("\n" + "=" * width)
    print(f"{BOLD}{CYAN}{title.center(width)}{RESET}")
    if subtitle:
        print(f"{MAGENTA}{subtitle.center(width)}{RESET}")
    print("=" * width + "\n")


def print_metric_table(headers: List[str], rows: List[List[Any]], title: str = ""):
    """Imprime una tabla de métricas formateada con bordes."""
    if title:
        print(f"\n{BOLD}{YELLOW}>>> {title}{RESET}")
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    else:
        # Fallback simple
        header_line = " | ".join(str(h) for h in headers)
        print("-" * len(header_line))
        print(header_line)
        print("-" * len(header_line))
        for r in rows:
            print(" | ".join(str(c) for c in r))
        print("-" * len(header_line))
