"""
Pruebas unitarias para los algoritmos y el pipeline de primalidad.
"""
import unittest
from src.primality.small_primes import passes_small_primes_filter, SMALL_PRIMES
from src.primality.miller_rabin import MillerRabinTester
from src.primality.baillie_psw import BailliePSWTester
from src.primality.pipeline import PrimalityFilterPipeline


class TestPrimalityTesting(unittest.TestCase):
    """Verifica detección exacta de primos y rechazo estricto de compuestos."""

    def setUp(self):
        self.mr = MillerRabinTester(rounds=30)
        self.bpsw = BailliePSWTester()
        self.pipeline = PrimalityFilterPipeline(mr_rounds=30)

    def test_small_primes(self):
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 997]:
            self.assertTrue(self.mr.is_prime(p))
            self.assertTrue(self.bpsw.is_prime(p))

    def test_small_composites(self):
        for c in [4, 6, 8, 9, 10, 12, 14, 15, 21, 25, 27, 33, 35, 100]:
            self.assertFalse(self.mr.is_prime(c))
            self.assertFalse(self.bpsw.is_prime(c))

    def test_carmichael_numbers_rejected(self):
        # Números de Carmichael: engañan al test de Fermat clásico, pero Miller-Rabin los detecta
        carmichaels = [561, 1105, 1729, 2465, 2821, 6601]
        for c in carmichaels:
            self.assertFalse(self.mr.is_prime(c), f"Miller-Rabin falló en rechazar Carmichael {c}")
            self.assertFalse(self.bpsw.is_prime(c), f"Baillie-PSW falló en rechazar Carmichael {c}")

    def test_large_known_prime(self):
        # Primo grande conocido: 2^127 - 1 (Mersenne M12 (127 bits, ~39 cifras))
        m127 = (1 << 127) - 1
        self.assertTrue(self.mr.is_prime(m127))
        self.assertTrue(self.bpsw.is_prime(m127))

    def test_pipeline_on_mixed_batch(self):
        primes = [104729, 1299709, 15485863]
        composites = [104728, 1299710, 15485865, 104729 * 104729]
        all_numbers = primes + composites
        results = self.pipeline.process_batch(all_numbers)
        self.assertEqual(results["total_analyzed"], len(all_numbers))
        self.assertEqual(results["primes_found_count"], len(primes))
        self.assertEqual(sorted(results["primes_list"]), sorted(primes))


if __name__ == "__main__":
    unittest.main()
