"""
Gestor y Serializador de Llaves Criptográficas (KeyManager).
Permite persistencia, exportación a JSON, carga e inspección de pares de llaves y huellas digitales.
"""
import json
import hashlib
import os
from typing import Dict, Any, Optional, Tuple
from .rsa_cipher import RSACryptosystem
from .elgamal_cipher import ElGamalCryptosystem


class KeyManager:
    """Gestiona el almacenamiento, exportación y verificación de integridad de llaves."""

    @staticmethod
    def compute_fingerprint(value: int) -> str:
        """Calcula huella criptográfica SHA-256 en formato legible para verificación."""
        val_str = str(value).encode("utf-8")
        digest = hashlib.sha256(val_str).hexdigest()
        return ":".join(digest[i:i + 2] for i in range(0, 16, 2)).upper()

    @classmethod
    def export_rsa_keys(cls, cipher: RSACryptosystem) -> Dict[str, Any]:
        """Exporta par de llaves RSA a estructura serializable."""
        e, n = cipher.public_key
        d, _ = cipher.private_key
        return {
            "type": "RSA-40-Digits",
            "fingerprint": cls.compute_fingerprint(n),
            "public_key": {
                "e": str(e),
                "n": str(n),
                "modulus_digits": len(str(n)),
                "modulus_bits": n.bit_length()
            },
            "private_key": {
                "d": str(d),
                "exponent_digits": len(str(d))
            }
        }

    @classmethod
    def export_elgamal_keys(cls, cipher: ElGamalCryptosystem) -> Dict[str, Any]:
        """Exporta par de llaves ElGamal a estructura serializable."""
        p, g, y = cipher.public_key
        _, x = cipher.private_key
        return {
            "type": "ElGamal-40-Digits",
            "fingerprint": cls.compute_fingerprint(p),
            "public_key": {
                "p": str(p),
                "g": g,
                "y": str(y),
                "prime_digits": len(str(p)),
                "prime_bits": p.bit_length()
            },
            "private_key": {
                "x": str(x),
                "exponent_digits": len(str(x))
            }
        }

    @staticmethod
    def save_to_file(data: Dict[str, Any], filepath: str) -> None:
        """Guarda la estructura de llaves en un archivo JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_from_file(filepath: str) -> Dict[str, Any]:
        """Carga una estructura de llaves desde un archivo JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
