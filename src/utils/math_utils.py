"""
Funciones matemáticas auxiliares para teoría de números, aritmética modular
y transformaciones criptográficas.
"""
from typing import Tuple


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Algoritmo de Euclides Extendido.
    Encuentra enteros x e y tales que: a*x + b*y = mcd(a, b).
    
    Retorna:
        Tuple[g, x, y] donde g = mcd(a, b).
    """
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y


def mod_inverse(a: int, m: int) -> int:
    """
    Calcula el inverso modular de a módulo m tal que (a * inv) % m == 1.
    Lanza ValueError si a y m no son coprimos.
    """
    if m <= 0:
        raise ValueError(f"El módulo debe ser positivo, recibido: {m}")
    gcd, x, _ = extended_gcd(a % m, m)
    if gcd != 1:
        raise ValueError(f"El inverso modular no existe: mcd({a}, {m}) = {gcd} != 1")
    return (x % m + m) % m


def is_coprime(a: int, b: int) -> bool:
    """Verifica si dos enteros son coprimos (mcd == 1)."""
    import math
    return math.gcd(a, b) == 1


def jacobi_symbol(a: int, n: int) -> int:
    """
    Calcula el símbolo de Jacobi (a / n) para n impar y positivo.
    Utilizado en pruebas de primalidad avanzadas (Solovay-Strassen / Baillie-PSW).
    """
    if n <= 0 or n % 2 == 0:
        raise ValueError("n debe ser un entero impar positivo.")
    a = a % n
    t = 1
    while a != 0:
        while a % 2 == 0:
            a //= 2
            r = n % 8
            if r in (3, 5):
                t = -t
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            t = -t
        a = a % n
    return t if n == 1 else 0


def int_to_bytes(n: int, length: int = None, byteorder: str = 'big') -> bytes:
    """
    Convierte un entero positivo a bytes.
    Si length es None, utiliza el número mínimo de bytes necesarios.
    """
    if n < 0:
        raise ValueError("Solo enteros no negativos pueden convertirse a bytes.")
    if n == 0:
        return b'\x00' if length is None or length == 1 else b'\x00' * length
    needed = (n.bit_length() + 7) // 8
    if length is None:
        length = needed
    elif length < needed:
        raise ValueError(f"Longitud requerida {needed} excede length={length}")
    return n.to_bytes(length, byteorder=byteorder)


def bytes_to_int(b: bytes, byteorder: str = 'big') -> int:
    """Convierte bytes a un entero positivo."""
    return int.from_bytes(b, byteorder=byteorder)
