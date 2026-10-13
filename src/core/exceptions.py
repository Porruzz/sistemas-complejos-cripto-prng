"""
Excepciones personalizadas para el dominio del sistema.
"""


class ComplexCryptoError(Exception):
    """Excepción base para el sistema criptográfico y generador."""
    pass


class PRNGConfigError(ComplexCryptoError):
    """Error en los parámetros de configuración de la estrategia PRNG."""
    pass


class PrimalityError(ComplexCryptoError):
    """Error durante la verificación o prueba de primalidad."""
    pass


class CryptoError(ComplexCryptoError):
    """Error en operaciones criptográficas (cifrado, descifrado, padding)."""
    pass


class InvalidKeyError(CryptoError):
    """Error derivado de llaves criptográficas inválidas o incompatibles."""
    pass
