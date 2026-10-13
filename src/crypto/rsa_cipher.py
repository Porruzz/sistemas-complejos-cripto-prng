"""
Sistema Criptográfico Asimétrico RSA implementado con números primos grandes de 40 cifras.
Soporta cifrado/descifrado de:
1. Mensajes de texto UTF-8 de longitud arbitraria mediante fragmentación en bloques y padding PKCS#7.
2. Cifrado y descifrado directo de números enteros grandes (e.g. 40 cifras) con verificación algebraica.
"""
import math
import time
from typing import Dict, Any, List, Tuple, Optional
from src.core.interfaces import ICryptosystem
from src.core.exceptions import CryptoError, InvalidKeyError
from src.utils.math_utils import mod_inverse, bytes_to_int, int_to_bytes


class RSACryptosystem(ICryptosystem):
    """
    Cifrador RSA de llave pública.
    
    Genera llaves a partir de dos números primos grandes de 40 cifras descubiertos:
        Módulo n = p * q (~80 cifras decimales, ~260 bits)
        Función phi(n) = (p - 1) * (q - 1)
        Exponente público e coprimo con phi(n) (por defecto 65537)
        Exponente privado d = e^(-1) mod phi(n)
    """

    DEFAULT_E = 65537

    def __init__(self, p: Optional[int] = None, q: Optional[int] = None, e: int = DEFAULT_E):
        self._p: Optional[int] = None
        self._q: Optional[int] = None
        self._n: Optional[int] = None
        self._phi: Optional[int] = None
        self._e: int = e
        self._d: Optional[int] = None
        self._block_size: int = 0

        if p is not None and q is not None:
            self.setup_keys([p, q], e=e)

    @property
    def name(self) -> str:
        return "RSA Public-Key Cryptosystem (Large Primes)"

    @property
    def public_key(self) -> Tuple[int, int]:
        """Retorna la llave pública (e, n)."""
        if self._n is None:
            raise InvalidKeyError("Las llaves no han sido inicializadas.")
        return self._e, self._n

    @property
    def private_key(self) -> Tuple[int, int]:
        """Retorna la llave privada (d, n)."""
        if self._d is None or self._n is None:
            raise InvalidKeyError("Las llaves no han sido inicializadas.")
        return self._d, self._n

    @property
    def modulus(self) -> int:
        if self._n is None:
            raise InvalidKeyError("Módulo no inicializado.")
        return self._n

    @property
    def block_size_bytes(self) -> int:
        return self._block_size

    def setup_keys(self, primes: List[int], **kwargs: Any) -> Dict[str, Any]:
        """
        Configura el par de llaves a partir de una lista que contenga al menos 2 primos grandes.
        """
        if len(primes) < 2:
            raise InvalidKeyError("Se requieren al menos 2 números primos grandes para RSA.")

        p = primes[0]
        q = primes[1]

        if p == q:
            raise InvalidKeyError("Los primos p y q deben ser distintos para garantizar la seguridad de RSA.")

        self._p = p
        self._q = q
        self._n = p * q
        self._phi = (p - 1) * (q - 1)

        # Seleccionar exponente público e
        req_e = kwargs.get("e", self.DEFAULT_E)
        if math.gcd(req_e, self._phi) == 1:
            self._e = req_e
        else:
            # Buscar el menor impar coprimo mayor a 3
            candidate_e = 3
            while math.gcd(candidate_e, self._phi) != 1:
                candidate_e += 2
            self._e = candidate_e

        # Calcular exponente privado d = e^(-1) mod phi
        self._d = mod_inverse(self._e, self._phi)

        # Tamaño seguro de bloque en bytes para m < n
        # Un bloque de B bytes puede tomar un valor máximo de 256^B - 1
        # Aseguramos que 256^B <= n - 1
        n_bits = self._n.bit_length()
        self._block_size = max(1, (n_bits - 1) // 8)

        return {
            "p_digits": len(str(self._p)),
            "q_digits": len(str(self._q)),
            "modulus_digits": len(str(self._n)),
            "modulus_bits": n_bits,
            "public_exponent_e": self._e,
            "private_exponent_d_digits": len(str(self._d)),
            "block_size_bytes": self._block_size
        }

    # =========================================================================
    # Cifrado y Descifrado de Mensajes de Texto
    # =========================================================================

    def encrypt_message(self, plaintext: str) -> Dict[str, Any]:
        """
        Cifra una cadena de texto UTF-8 de cualquier longitud.
        Fragmenta en bloques de tamaño B con padding PKCS#7.
        """
        if self._n is None or self._e is None:
            raise InvalidKeyError("Sistema RSA no inicializado con llaves válidas.")

        data_bytes = plaintext.encode("utf-8")
        bs = self._block_size

        # Aplicar padding PKCS#7 al mensaje total para alinear con el tamaño de bloque
        pad_len = bs - (len(data_bytes) % bs)
        padded_bytes = data_bytes + bytes([pad_len] * pad_len)

        # Dividir en bloques
        blocks = [padded_bytes[i:i + bs] for i in range(0, len(padded_bytes), bs)]

        t_start = time.perf_counter()
        cipher_blocks: List[str] = []

        for b in blocks:
            m_int = bytes_to_int(b)
            if m_int >= self._n:
                raise CryptoError("Bloque de mensaje excede el módulo n.")
            # Cifrado RSA: c = m^e mod n
            c_int = pow(m_int, self._e, self._n)
            cipher_blocks.append(str(c_int))

        elapsed = time.perf_counter() - t_start

        return {
            "algorithm": self.name,
            "block_size_bytes": bs,
            "block_count": len(cipher_blocks),
            "cipher_blocks": cipher_blocks,
            "encryption_time_sec": round(elapsed, 6)
        }

    def decrypt_message(self, ciphertext_payload: Dict[str, Any]) -> str:
        """
        Descifra un payload generado por encrypt_message y reconstruye la cadena original.
        """
        if self._n is None or self._d is None:
            raise InvalidKeyError("Llave privada no disponible para descifrar.")

        cipher_blocks = ciphertext_payload.get("cipher_blocks", [])
        bs = ciphertext_payload.get("block_size_bytes", self._block_size)

        decrypted_raw = bytearray()
        for c_str in cipher_blocks:
            c_int = int(c_str)
            # Descifrado RSA: m = c^d mod n
            m_int = pow(c_int, self._d, self._n)
            block_bytes = int_to_bytes(m_int, length=bs)
            decrypted_raw.extend(block_bytes)

        # Quitar padding PKCS#7
        if not decrypted_raw:
            return ""

        pad_len = decrypted_raw[-1]
        if pad_len == 0 or pad_len > bs or decrypted_raw[-pad_len:] != bytes([pad_len] * pad_len):
            raise CryptoError("Fallo de integridad: Padding PKCS#7 inválido o mensaje corrupto.")

        clean_bytes = bytes(decrypted_raw[:-pad_len])
        return clean_bytes.decode("utf-8")

    # =========================================================================
    # Cifrado y Descifrado Directo de Números
    # =========================================================================

    def encrypt_number(self, number: int) -> int:
        """
        Cifra directamente un número entero (e.g. un número de 40 cifras).
        Garantiza que number < n (dado que n tiene ~80 cifras, cualquier número
        de 40 cifras satisface estrictamente number < n).
        
        Operación: C = number^e mod n
        """
        if self._n is None or self._e is None:
            raise InvalidKeyError("Llaves no inicializadas.")
        if number < 0:
            raise CryptoError("Solo números enteros no negativos pueden ser cifrados.")
        if number >= self._n:
            raise CryptoError(f"El número a cifrar ({number}) excede el módulo RSA ({self._n}).")

        return pow(number, self._e, self._n)

    def decrypt_number(self, ciphertext_number: int) -> int:
        """
        Descifra directamente un número entero previamente cifrado con encrypt_number.
        
        Operación: M = ciphertext^d mod n
        """
        if self._n is None or self._d is None:
            raise InvalidKeyError("Llave privada no inicializada.")
        if ciphertext_number < 0 or ciphertext_number >= self._n:
            raise CryptoError("Criptograma numérico inválido fuera del rango [0, n - 1].")

        return pow(ciphertext_number, self._d, self._n)
