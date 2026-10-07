import csv
from collections import Counter
import itertools
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from permutation_gate import information, permutation_test, permute_within_strata, demo_rows

ROOT = Path(__file__).resolve().parents[1]


class PermutationGateTests(unittest.TestCase):
    def test_known_one_bit_gain(self):
        self.assertEqual(information([(0, 0, 0), (1, 0, 1)] * 20), (1.0, 1.0))

    def test_balanced_independence(self):
        self.assertEqual(information(list(itertools.product(range(2), repeat=3))), (0.0, 1.0))

    def test_screened_off_layer_has_no_increment(self):
        rows = [(t, w1, w1) for t, w1 in itertools.product(range(2), repeat=2)] * 10
        self.assertEqual(information(rows), (0.0, 1.0))
        result = permutation_test(rows)
        self.assertEqual(result['status'], 'could_not_run')
        self.assertIsNone(result['monte_carlo_p'])

    def test_exhaustive_null_matches_analytic_probability(self):
        # Six equally likely assignments of two flags to four rows. Two yield
        # one bit of CMI and four yield 0: exact upper-tail probability is 1/3.
        original = [(0, 'lower', 0), (0, 'lower', 0), (1, 'lower', 1), (1, 'lower', 1)]
        assignments = set(itertools.permutations([0, 0, 1, 1]))
        null = [information([(r[0], r[1], v) for r, v in zip(original, values)])[0]
                for values in assignments]
        self.assertAlmostEqual(sum(x >= 1 for x in null) / len(null), 1/3)
        result = permutation_test(original, permutations=3999, seed=13)
        self.assertAlmostEqual(result['monte_carlo_p'], 1/3, delta=0.035)
        self.assertEqual(result['status'], 'no_gain_resolved')

    def test_strata_and_margins_are_preserved(self):
        rows = list(itertools.product(range(3), range(4), range(2))) * 3
        shuffled = permute_within_strata(rows, random.Random(7))
        self.assertEqual([(a, b) for a, b, c in rows], [(a, b) for a, b, c in shuffled])
        self.assertEqual(Counter((b, c) for a, b, c in rows), Counter((b, c) for a, b, c in shuffled))
        self.assertEqual(rows, list(itertools.product(range(3), range(4), range(2))) * 3)
        self.assertNotEqual(rows, shuffled)

    def test_strong_signal_and_positive_p_value(self):
        result = permutation_test([(0, 0, 0), (1, 0, 1)] * 30, permutations=99)
        self.assertEqual(result['monte_carlo_p'], 0.01)
        self.assertEqual(result['status'], 'gain_resolved')

    def test_ties_are_counted(self):
        result = permutation_test(list(itertools.product(range(2), repeat=3)), permutations=99)
        self.assertEqual(result['monte_carlo_p'], 1.0)
        self.assertEqual(result['status'], 'no_gain_resolved')

    def test_no_residual_uncertainty(self):
        result = permutation_test([(0, 0, 0), (1, 1, 1)])
        self.assertEqual(result['status'], 'could_not_run')
        self.assertIsNone(result['normalized_gain'])
        json.dumps(result, allow_nan=False)

    def test_reproducible_without_global_rng_effect(self):
        rows = demo_rows('design-b', 100, 3)
        state = random.getstate()
        self.assertEqual(permutation_test(rows, permutations=99, seed=4),
                         permutation_test(rows, permutations=99, seed=4))
        self.assertEqual(state, random.getstate())

    def test_invalid_inputs(self):
        for rows in [[], [(1, 2)], [(1, None, 2)], [(1, float('nan'), 2)], [(1, '', 2)]]:
            with self.assertRaises((ValueError, TypeError)):
                permutation_test(rows)
        for options in [dict(alpha=0), dict(alpha=1), dict(permutations=1), dict(permutations=0), dict(permutations=True)]:
            with self.assertRaises(ValueError):
                permutation_test([(0, 0, 0), (1, 0, 1)], **options)

    def test_csv_declarations_required_and_valid_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.csv'
            path.write_text('T,W1,W2\n0,0,0\n1,0,1\n' * 1)
            command = [sys.executable, str(ROOT / 'permutation_gate.py'), '--csv', str(path)]
            rejected = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            for name in ['target', 'boundary', 'ordering', 'regime']:
                command.extend(['--' + name, 'declared'])
            accepted = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertFalse(json.loads(accepted.stdout)['synthetic'])

    def test_original_scripts_still_reproduce_reported_values(self):
        gate = subprocess.check_output([sys.executable, str(ROOT / 'watcher_gate.py')], text=True)
        self.assertIn('0.0791 bits', gate)
        self.assertIn('25.9%', gate)
        estimation = subprocess.check_output([sys.executable, str(ROOT / 'estimation.py')], text=True)
        self.assertIn('95th pct = 0.0427 bits', estimation)
        self.assertIn('54.8% of residual', estimation)


if __name__ == '__main__':
    unittest.main()
