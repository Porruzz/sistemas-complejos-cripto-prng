"""Módulo central con interfaces y excepciones."""
from .interfaces import IPRNGStrategy, IPrimalityTester, ICryptosystem
from .exceptions import ComplexCryptoError, PRNGConfigError, PrimalityError, CryptoError, InvalidKeyError

__all__ = [
    "IPRNGStrategy",
    "IPrimalityTester",
    "ICryptosystem",
    "ComplexCryptoError",
    "PRNGConfigError",
    "PrimalityError",
    "CryptoError",
    "InvalidKeyError"
]
