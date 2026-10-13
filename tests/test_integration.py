"""
Prueba de Integración End-to-End: Generación, Detección de Primos, Cifrado de Mensajes y Números.
"""
import unittest
from src.prng.machine import PseudoRandomMachine
from src.primality.pipeline import PrimalityFilterPipeline
from src.crypto.rsa_cipher import RSACryptosystem
from src.crypto.elgamal_cipher import ElGamalCryptosystem


class TestEndToEndIntegration(unittest.TestCase):
    """Flujo completo integrado del examen."""

    def test_full_pipeline_flow(self):
        # 1. Configurar la máquina pseudoaleatoria con una técnica
        machine = PseudoRandomMachine(technique="rule30", seed=20261013)

        # 2. Generar una muestra de números de 40 cifras
        # Usamos 500 para una prueba rápida de integración
        batch = machine.generate_batch(count=500, digits=40)
        self.assertEqual(len(batch["numbers"]), 500)
        for n in batch["numbers"]:
            self.assertEqual(len(str(n)), 40)

        # 3. Filtrar primos mediante el pipeline
        pipeline = PrimalityFilterPipeline(mr_rounds=25)
        primality_results = pipeline.process_batch(batch["numbers"])

        # Si en los 500 números hubo primos, usarlos; de lo contrario generar candidatos
        primes = primality_results["primes_list"]
        if len(primes) < 2:
            # Enriquecer buscando primos adicionales de 40 cifras
            while len(primes) < 2:
                cand = machine.generate_single_number(40)
                if pipeline.test_single(cand):
                    primes.append(cand)

        p, q = primes[0], primes[1]
        self.assertEqual(len(str(p)), 40)
        self.assertEqual(len(str(q)), 40)

        # 4. Inicializar sistema de encriptación con los primos encontrados
        rsa = RSACryptosystem(p, q)

        # 5. Cifrado y descifrado de mensaje
        test_msg = "Prueba de integración exitosa: Parcial 2 Sistemas Complejos."
        cipher_msg = rsa.encrypt_message(test_msg)
        recovered_msg = rsa.decrypt_message(cipher_msg)
        self.assertEqual(recovered_msg, test_msg)

        # 6. Cifrado y descifrado de los números primos encontrados
        c_p = rsa.encrypt_number(p)
        rec_p = rsa.decrypt_number(c_p)
        self.assertEqual(rec_p, p)

        c_q = rsa.encrypt_number(q)
        rec_q = rsa.decrypt_number(c_q)
        self.assertEqual(rec_q, q)

        # 7. Cifrado ElGamal usando un primo
        elg = ElGamalCryptosystem(p)
        elg_cipher = elg.encrypt_message("Mensaje ElGamal verificado")
        self.assertEqual(elg.decrypt_message(elg_cipher), "Mensaje ElGamal verificado")


if __name__ == "__main__":
    unittest.main()
