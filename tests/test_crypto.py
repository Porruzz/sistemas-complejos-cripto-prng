"""
Pruebas unitarias para los sistemas criptográficos RSA y ElGamal con primos grandes de 40 cifras.
"""
import unittest
from src.primality.miller_rabin import MillerRabinTester
from src.crypto.rsa_cipher import RSACryptosystem
from src.crypto.elgamal_cipher import ElGamalCryptosystem
from src.crypto.key_manager import KeyManager


def generate_test_prime_40_digits(offset: int) -> int:
    """Genera un primo real de 40 cifras para propósitos de prueba."""
    mr = MillerRabinTester(rounds=25)
    cand = 10**39 + offset
    if cand % 2 == 0:
        cand += 1
    while not mr.is_prime(cand):
        cand += 2
    return cand


class TestCryptosystems(unittest.TestCase):
    """Verifica el cifrado/descifrado de mensajes y números usando primos grandes."""

    @classmethod
    def setUpClass(cls):
        cls.p1 = generate_test_prime_40_digits(103)
        cls.p2 = generate_test_prime_40_digits(759)
        assert len(str(cls.p1)) == 40
        assert len(str(cls.p2)) == 40
        assert cls.p1 != cls.p2

    def test_rsa_setup_and_message_roundtrip(self):
        rsa = RSACryptosystem(self.p1, self.p2)
        messages = [
            "Mensaje simple",
            "Parcial 2 - Sistemas Complejos: Encriptación con primos de 40 cifras.",
            "Caracteres especiales y acentos: áéíóú ñ ¿¡! #$%&*()",
            "A" * 150  # Mensaje largo que abarca múltiples bloques
        ]
        for msg in messages:
            cipher_payload = rsa.encrypt_message(msg)
            decrypted = rsa.decrypt_message(cipher_payload)
            self.assertEqual(decrypted, msg, f"Fallo en descifrado RSA para mensaje: {msg}")

    def test_rsa_number_encryption_roundtrip(self):
        """Verifica el requisito explícito: 'Realizar pruebas de encriptación de los numeros'."""
        rsa = RSACryptosystem(self.p1, self.p2)
        test_numbers = [
            123456789,
            10**39 + 42,
            self.p1,  # Cifrar uno de los primos de 40 cifras
            self.p2,
            9876543210987654321098765432109876543210  # Número de 40 cifras arbitrario
        ]
        for num in test_numbers:
            c = rsa.encrypt_number(num)
            self.assertNotEqual(c, num, "El criptograma no debe ser idéntico al número original")
            m = rsa.decrypt_number(c)
            self.assertEqual(m, num, f"Fallo en descifrado numérico RSA para: {num}")

    def test_elgamal_setup_and_roundtrip(self):
        elg = ElGamalCryptosystem(self.p1)
        msg = "Mensaje ElGamal seguro"
        payload = elg.encrypt_message(msg)
        decrypted = elg.decrypt_message(payload)
        self.assertEqual(decrypted, msg)

        # Cifrado numérico directo m < p
        num = 12345678901234567890
        pair = elg.encrypt_number(num)
        recov = elg.decrypt_number(pair)
        self.assertEqual(recov, num)

    def test_key_manager_export(self):
        rsa = RSACryptosystem(self.p1, self.p2)
        rsa_keys = KeyManager.export_rsa_keys(rsa)
        self.assertEqual(rsa_keys["type"], "RSA-40-Digits")
        self.assertIn("fingerprint", rsa_keys)

        elg = ElGamalCryptosystem(self.p1)
        elg_keys = KeyManager.export_elgamal_keys(elg)
        self.assertEqual(elg_keys["type"], "ElGamal-40-Digits")


if __name__ == "__main__":
    unittest.main()
