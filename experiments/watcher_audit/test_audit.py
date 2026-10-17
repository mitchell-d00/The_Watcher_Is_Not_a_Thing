import itertools
import unittest
from audit import MetaWatcher, generate, residual


class AuditTests(unittest.TestCase):
    def test_exact_xor_requires_joint_panel(self):
        rows = [(a ^ b, {'left': a, 'right': b})
                for a, b in itertools.product(range(2), repeat=2)] * 32
        self.assertEqual(residual(rows, ('left',)), 1)
        self.assertEqual(residual(rows, ('right',)), 1)
        self.assertEqual(residual(rows, ('left', 'right')), 0)
        self.assertEqual(MetaWatcher().fit(rows).panel, ('left', 'right'))

    def test_distinct_panel_excludes_duplicate_noise_stuck(self):
        panel = MetaWatcher().fit(generate(0)).panel
        self.assertEqual(panel, ('watch_a', 'watch_b'))

    def test_fresh_data_confirms_each_contribution(self):
        report = MetaWatcher().fit(generate(0)).audit(generate(1))
        self.assertTrue(report['all_selected_contributions_detected'])
        self.assertFalse(report['missing_target_information_alert'])

    def test_copy_failure_is_detected_without_deleting_both(self):
        auditor = MetaWatcher().fit(generate(0))
        report = auditor.audit(generate(1, mode='copy_failure'))
        self.assertTrue(report['missing_target_information_alert'])
        self.assertFalse(report['all_selected_contributions_detected'])
        self.assertGreater(report['residual_target_bits'], 0.9)
        self.assertEqual(auditor.panel, ('watch_a', 'watch_b'))

    def test_unfitted_auditor_rejects_run(self):
        with self.assertRaises(ValueError):
            MetaWatcher().audit(generate(0))

    def test_constant_target_selects_no_monitors(self):
        rows = [(0, {'a': i % 2}) for i in range(100)]
        self.assertEqual(MetaWatcher().fit(rows).panel, ())

    def test_discovery_and_validation_differ(self):
        self.assertNotEqual(generate(0), generate(1))


if __name__ == '__main__':
    unittest.main()
