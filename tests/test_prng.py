"""
Pruebas unitarias para las técnicas PRNG y la Máquina Pseudoaleatoria.
"""
import unittest
from src.prng.rule30_ca import WolframRule30Strategy
from src.prng.chaotic_map import ChaoticLogisticStrategy
from src.prng.blum_blum_shub import BlumBlumShubStrategy
from src.prng.lcg_strategy import LCGStrategy
from src.prng.factory import PRNGFactory
from src.prng.machine import PseudoRandomMachine


class TestPRNGStrategies(unittest.TestCase):
    """Verifica que cada técnica PRNG cumpla con los contratos matemáticos y de 40 cifras."""

    def test_rule30_40_digits(self):
        strategy = WolframRule30Strategy(seed=123456789, warmup_steps=50)
        num = strategy.generate_number(40)
        self.assertIsInstance(num, int)
        self.assertEqual(len(str(num)), 40)
        self.assertGreaterEqual(num, 10**39)
        self.assertLess(num, 10**40)

    def test_chaotic_logistic_40_digits(self):
        strategy = ChaoticLogisticStrategy(seed=0.456, r=4.0, warmup_steps=100)
        num = strategy.generate_number(40)
        self.assertIsInstance(num, int)
        self.assertEqual(len(str(num)), 40)
        self.assertGreaterEqual(num, 10**39)
        self.assertLess(num, 10**40)

    def test_blum_blum_shub_40_digits(self):
        strategy = BlumBlumShubStrategy(seed=987654321)
        num = strategy.generate_number(40)
        self.assertIsInstance(num, int)
        self.assertEqual(len(str(num)), 40)
        self.assertGreaterEqual(num, 10**39)
        self.assertLess(num, 10**40)

    def test_lcg_40_digits(self):
        strategy = LCGStrategy(seed=42)
        num = strategy.generate_number(40)
        self.assertIsInstance(num, int)
        self.assertEqual(len(str(num)), 40)
        self.assertGreaterEqual(num, 10**39)
        self.assertLess(num, 10**40)

    def test_factory_creation(self):
        s1 = PRNGFactory.create("rule30")
        s2 = PRNGFactory.create("logistic")
        s3 = PRNGFactory.create("bbs")
        self.assertIsInstance(s1, WolframRule30Strategy)
        self.assertIsInstance(s2, ChaoticLogisticStrategy)
        self.assertIsInstance(s3, BlumBlumShubStrategy)

    def test_machine_facade(self):
        machine = PseudoRandomMachine(technique="rule30", seed=42)
        single = machine.generate_single_number(digits=40)
        self.assertEqual(len(str(single)), 40)

        # Batch pequeño para test rápido
        batch = machine.generate_batch(count=20, digits=40)
        self.assertEqual(batch["count"], 20)
        self.assertEqual(len(batch["numbers"]), 20)
        for n in batch["numbers"]:
            self.assertEqual(len(str(n)), 40)


if __name__ == "__main__":
    unittest.main()
