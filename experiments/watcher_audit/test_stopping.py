import itertools
import math
import unittest
from stopping import certify, continuity


class StoppingTests(unittest.TestCase):
    def test_stop_does_not_require_target_already_solved(self):
        c = {(t,0,a,b):31250 for t,a,b in itertools.product(range(2), repeat=3)}
        r = certify(c, (2,1,2,2))
        self.assertEqual(r['status'], 'stop_within_declared_scope')
        self.assertTrue(all(g['estimate_bits'] == 0 for g in r['groups']))

    def test_redundancy_can_certify_stop(self):
        counts = {(a, a, a, b): 62500 for a, b in itertools.product(range(2), repeat=2)}
        r = certify(counts, (2, 2, 2, 2))
        self.assertEqual(r['status'], 'stop_within_declared_scope')
        self.assertTrue(all(g['lower_bits'] <= 0 <= g['upper_bits'] for g in r['groups']))

    def test_xor_continue_despite_individually_useless_candidates(self):
        counts = {(a ^ b, 0, a, b): 62500 for a, b in itertools.product(range(2), repeat=2)}
        r = certify(counts, (2, 1, 2, 2))
        self.assertEqual(r['status'], 'continue')
        self.assertEqual([g['estimate_bits'] for g in r['groups']], [0, 0, 1])
        self.assertGreater(r['groups'][-1]['lower_bits'], .25)

    def test_partial_search_cannot_stop_on_xor(self):
        c = {(a ^ b, 0, a, b): 62500 for a, b in itertools.product(range(2), repeat=2)}
        self.assertEqual(certify(c, (2, 1, 2, 2), max_group=1)['status'], 'inconclusive')

    def test_small_sample_remains_inconclusive(self):
        c = {(a ^ b, 0, a, b): 8 for a, b in itertools.product(range(2), repeat=2)}
        self.assertEqual(certify(c, (2, 1, 2, 2))['status'], 'inconclusive')

    def test_unseen_cells_still_count_in_bound(self):
        c = {(0, 0, 0): 100}
        small = certify(c, (2, 2, 2))
        large = certify(c, (20, 20, 20))
        self.assertGreater(large['tv_radius'], small['tv_radius'])
        self.assertEqual(large['status'], 'inconclusive')

    def test_more_data_narrows_interval(self):
        c = {(a ^ b, 0, a, b): 100 for a, b in itertools.product(range(2), repeat=2)}
        lo = certify(c, (2, 1, 2, 2))
        hi = certify({r:n*1000 for r,n in c.items()}, (2, 1, 2, 2))
        self.assertLess(hi['tv_radius'], lo['tv_radius'])

    def test_entropy_continuity_endpoints(self):
        self.assertEqual(continuity(0, 4), 0)
        self.assertEqual(continuity(1, 1), 0)
        self.assertAlmostEqual(continuity(1, 4), math.log2(4))

    def test_reject_invalid_support_and_counts(self):
        for c, sizes in [({}, (2,2,2)), ({(2,0,0):1}, (2,2,2)),
                         ({(0,0,0):-1}, (2,2,2)), ({(0,0,0):1}, (0,2,2))]:
            with self.assertRaises(ValueError):
                certify(c, sizes)

    def test_singleton_target_has_zero_gain_bound(self):
        self.assertEqual(certify({(0,0,0):1}, (1,1,2))['groups'][0]['upper_bits'], 0)


if __name__ == '__main__':
    unittest.main()
