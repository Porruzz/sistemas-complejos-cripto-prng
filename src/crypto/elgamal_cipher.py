"""
Sistema Criptográfico Asimétrico ElGamal implementado sobre un número primo grande de 40 cifras.
Fundamento: Dificultad del Problema del Logaritmo Discreto (DLP) en Z_p^*.
"""
import random
import math
import time
from typing import Dict, Any, List, Tuple, Optional
from src.core.interfaces import ICryptosystem
from src.core.exceptions import CryptoError, InvalidKeyError
from src.utils.math_utils import mod_inverse, bytes_to_int, int_to_bytes, is_coprime


class ElGamalCryptosystem(ICryptosystem):
    """
    Cifrador de llave pública ElGamal.
    Opera directamente sobre un primo grande p de 40 cifras descubierto por la máquina.
    
    Estructura algebraica:
        Grupo multiplicativo (Z_p)*
        Generador/Base g
        Llave privada: entero x in [2, p - 2]
        Llave pública: (p, g, y) donde y = g^x mod p
    """

    def __init__(self, p: Optional[int] = None, g: int = 2):
        self._p: Optional[int] = None
        self._g: int = g
        self._x: Optional[int] = None  # Llave privada
        self._y: Optional[int] = None  # Llave pública
        self._block_size: int = 0

        if p is not None:
            self.setup_keys([p], g=g)

    @property
    def name(self) -> str:
        return "ElGamal Public-Key Cryptosystem (Discrete Logarithm)"

    @property
    def public_key(self) -> Tuple[int, int, int]:
        """Retorna (p, g, y)."""
        if self._p is None or self._y is None:
            raise InvalidKeyError("Llaves no inicializadas.")
        return self._p, self._g, self._y

    @property
    def private_key(self) -> Tuple[int, int]:
        """Retorna (p, x)."""
        if self._p is None or self._x is None:
            raise InvalidKeyError("Llaves no inicializadas.")
        return self._p, self._x

    @property
    def modulus(self) -> int:
        if self._p is None:
            raise InvalidKeyError("Módulo no inicializado.")
        return self._p

    def setup_keys(self, primes: List[int], **kwargs: Any) -> Dict[str, Any]:
        """
        Configura el sistema ElGamal usando al menos un número primo grande p.
        """
        if not primes:
            raise InvalidKeyError("Se requiere al menos un número primo para ElGamal.")

        self._p = primes[0]
        self._g = kwargs.get("g", 2)

        # Si g^((p-1)/2) == 1 mod p, probar bases alternativas para maximizar el orden del subgrupo
        if pow(self._g, (self._p - 1) // 2, self._p) == 1:
            for candidate_g in [3, 5, 7, 11, 13]:
                if pow(candidate_g, (self._p - 1) // 2, self._p) != 1:
                    self._g = candidate_g
                    break

        # Generar llave privada aleatoria x in [2, p - 2]
        self._x = random.randrange(2, self._p - 1)

        # Llave pública y = g^x mod p
        self._y = pow(self._g, self._x, self._p)

        # Tamaño de bloque seguro en bytes: 256^B < p
        p_bits = self._p.bit_length()
        self._block_size = max(1, (p_bits - 1) // 8)

        return {
            "prime_p_digits": len(str(self._p)),
            "prime_p_bits": p_bits,
            "generator_g": self._g,
            "public_key_y_digits": len(str(self._y)),
            "block_size_bytes": self._block_size
        }

    # =========================================================================
    # Cifrado y Descifrado Directo de Números
    # =========================================================================

    def encrypt_number(self, number: int) -> Tuple[int, int]:  # type: ignore
        """
        Cifra directamente un entero numérico m < p.
        Retorna el par de texto cifrado (c1, c2):
            c1 = g^k mod p
            c2 = (m * y^k) mod p
        donde k es una llave efímera aleatoria coprima con p - 1.
        """
        if self._p is None or self._y is None:
            raise InvalidKeyError("Sistema ElGamal no inicializado.")
        if number < 0:
            raise CryptoError("Solo números positivos o cero pueden ser cifrados.")
        if number >= self._p:
            raise CryptoError(f"El número ({number}) excede el módulo primo p ({self._p}).")

        # Seleccionar secreto efímero k
        p_minus_1 = self._p - 1
        k = random.randrange(2, p_minus_1)
        while not is_coprime(k, p_minus_1):
            k = random.randrange(2, p_minus_1)

        c1 = pow(self._g, k, self._p)
        s = pow(self._y, k, self._p)  # Secreto compartido
        c2 = (number * s) % self._p

        return c1, c2

    def decrypt_number(self, ciphertext_tuple: Tuple[int, int]) -> int:  # type: ignore
        """
        Descifra una tupla (c1, c2) numérico:
            s = c1^x mod p
            m = (c2 * s^(-1)) mod p
        """
        if self._p is None or self._x is None:
            raise InvalidKeyError("Llave privada no disponible.")

        c1, c2 = ciphertext_tuple
        s = pow(c1, self._x, self._p)
        s_inv = mod_inverse(s, self._p)
        m = (c2 * s_inv) % self._p
        return m

    # =========================================================================
    # Cifrado y Descifrado de Mensajes de Texto
    # =========================================================================

    def encrypt_message(self, plaintext: str) -> Dict[str, Any]:
        """Cifra un mensaje UTF-8 mediante fragmentación de bloques y ElGamal."""
        if self._p is None or self._y is None:
            raise InvalidKeyError("Sistema no inicializado.")

        data_bytes = plaintext.encode("utf-8")
        bs = self._block_size

        pad_len = bs - (len(data_bytes) % bs)
        padded_bytes = data_bytes + bytes([pad_len] * pad_len)
        blocks = [padded_bytes[i:i + bs] for i in range(0, len(padded_bytes), bs)]

        t_start = time.perf_counter()
        cipher_pairs: List[Tuple[str, str]] = []

        for b in blocks:
            m_int = bytes_to_int(b)
            c1, c2 = self.encrypt_number(m_int)
            cipher_pairs.append((str(c1), str(c2)))

        elapsed = time.perf_counter() - t_start

        return {
            "algorithm": self.name,
            "block_size_bytes": bs,
            "block_count": len(cipher_pairs),
            "cipher_pairs": cipher_pairs,
            "encryption_time_sec": round(elapsed, 6)
        }

    def decrypt_message(self, ciphertext_payload: Dict[str, Any]) -> str:
        """Descifra el payload de pares ElGamal y reconstruye la cadena original."""
        if self._p is None or self._x is None:
            raise InvalidKeyError("Llave privada no disponible.")

        cipher_pairs = ciphertext_payload.get("cipher_pairs", [])
        bs = ciphertext_payload.get("block_size_bytes", self._block_size)

        decrypted_raw = bytearray()
        for c1_str, c2_str in cipher_pairs:
            pair = (int(c1_str), int(c2_str))
            m_int = self.decrypt_number(pair)
            block_bytes = int_to_bytes(m_int, length=bs)
            decrypted_raw.extend(block_bytes)

        if not decrypted_raw:
            return ""

        pad_len = decrypted_raw[-1]
        if pad_len == 0 or pad_len > bs or decrypted_raw[-pad_len:] != bytes([pad_len] * pad_len):
            raise CryptoError("Fallo de integridad: Padding PKCS#7 inválido en ElGamal.")

        clean_bytes = bytes(decrypted_raw[:-pad_len])
        return clean_bytes.decode("utf-8")
