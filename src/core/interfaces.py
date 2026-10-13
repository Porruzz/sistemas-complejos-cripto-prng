"""
Interfaces fundamentales y contratos del sistema.
Patrón Strategy para generadores PRNG, contratos para probadores de primalidad
y contratos de sistemas criptográficos asimétricos.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IPRNGStrategy(ABC):
    """
    Contrato base (Patrón Strategy) para algoritmos generadores de números pseudoaleatorios.
    Permite intercambiar de forma transparente diferentes técnicas matemáticas y dinámicas.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre formal de la técnica."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción teórica y fundamentos del método."""
        pass

    @abstractmethod
    def configure(self, **kwargs: Any) -> None:
        """Configura los parámetros específicos de la estrategia (semillas, constantes, etc.)."""
        pass

    @abstractmethod
    def next_bit(self) -> int:
        """Retorna el siguiente bit pseudoaleatorio (0 o 1)."""
        pass

    @abstractmethod
    def next_bits(self, count: int) -> int:
        """Retorna un entero compuesto por `count` bits pseudoaleatorios."""
        pass

    @abstractmethod
    def generate_number(self, digits: int = 40) -> int:
        """
        Genera un número entero positivo pseudoaleatorio de exactamente `digits` cifras.
        Garantiza que la primera cifra esté en [1, 9] para que len(str(N)) == digits.
        """
        pass


class IPrimalityTester(ABC):
    """Contrato base para verificadores de primalidad."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del algoritmo de prueba."""
        pass

    @abstractmethod
    def is_prime(self, candidate: int) -> bool:
        """Retorna True si el candidato es primo (o probablemente primo con alta certeza)."""
        pass


class ICryptosystem(ABC):
    """
    Contrato base para sistemas criptográficos de llave pública fundamentados
    en la dificultad de problemas sobre números primos grandes.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del sistema criptográfico (e.g., RSA, ElGamal)."""
        pass

    @abstractmethod
    def setup_keys(self, primes: List[int], **kwargs: Any) -> Dict[str, Any]:
        """
        Genera y configura el par de llaves (pública y privada) utilizando los primos provistos.
        """
        pass

    @abstractmethod
    def encrypt_message(self, plaintext: str) -> Dict[str, Any]:
        """Cifra un mensaje de texto plano arbitrario (UTF-8)."""
        pass

    @abstractmethod
    def decrypt_message(self, ciphertext_payload: Dict[str, Any]) -> str:
        """Descifra el mensaje cifrado retornando la cadena de texto original."""
        pass

    @abstractmethod
    def encrypt_number(self, number: int) -> int:
        """Cifra directamente un valor numérico entero grande."""
        pass

    @abstractmethod
    def decrypt_number(self, ciphertext_number: int) -> int:
        """Descifra directamente un valor numérico entero grande."""
        pass
