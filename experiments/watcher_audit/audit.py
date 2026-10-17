"""Synthetic watcher-of-watchers experiment. Standard library only."""
import itertools
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from permutation_gate import permutation_test


def entropy(values):
    import math
    counts = Counter(values)
    n = len(values)
    return -sum(c / n * math.log2(c / n) for c in counts.values())


def residual(rows, names):
    joint = [(t, tuple(w[n] for n in names)) for t, w in rows]
    return max(0.0, entropy(joint) - entropy([x for _, x in joint]))


def generate(seed, n=1024, mode='separate'):
    """Independent observations; target labels available after each episode."""
    if mode not in ('separate', 'copy_failure', 'xor'):
        raise ValueError('unknown scenario')
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        a, b, noise = [rng.randrange(2) for _ in range(3)]
        if mode == 'xor':
            target, outputs = a ^ b, {'left': a, 'right': b}
        else:
            target = (a, b)
            outputs = {'watch_a': a, 'copy_a': a,
                       'watch_b': a if mode == 'copy_failure' else b,
                       'noise': noise, 'stuck': 0}
        rows.append((target, outputs))
    return rows


class MetaWatcher:
    """Select a joint panel on discovery data, audit on fresh labeled data.

    Exhaustive subset search prevents a greedy zero-gain stop from losing XOR.
    This small categorical toy uses empirical entropy for panel selection.
    It does not certify population equivalence or generalize to large systems.
    """
    def __init__(self, tolerance_bits=0.01, min_gain_bits=0.05,
                 alpha=0.05, permutations=999):
        self.tolerance = tolerance_bits
        self.min_gain = min_gain_bits
        self.alpha = alpha
        self.permutations = permutations
        self.panel = None

    def fit(self, discovery):
        names = tuple(discovery[0][1])
        if len(names) > 10:
            raise ValueError('exhaustive experiment limited to 10 monitors')
        floor = residual(discovery, names)
        for size in range(len(names) + 1):
            candidates = list(itertools.combinations(names, size))
            eligible = [s for s in candidates
                        if residual(discovery, s) <= floor + self.tolerance]
            if eligible:
                self.panel = min(eligible, key=lambda s: residual(discovery, s))
                break
        return self

    def audit(self, validation):
        if self.panel is None:
            raise ValueError('fit before audit')
        names = tuple(validation[0][1])
        tests = {}
        for name in self.panel:
            others = tuple(n for n in self.panel if n != name)
            rows = [(t, tuple(w[n] for n in others), w[name])
                    for t, w in validation]
            result = permutation_test(rows, permutations=self.permutations,
                                      alpha=self.alpha / max(1, len(self.panel)), seed=71)
            tests[name] = {'gain_bits': result['observed_cmi_bits'],
                           'p': result['monte_carlo_p'],
                           'distinct_contribution_detected':
                           result['status'] == 'gain_resolved' and
                           result['observed_cmi_bits'] >= self.min_gain}
        exact_matches = [(a, b) for a, b in itertools.combinations(names, 2)
                         if all(w[a] == w[b] for _, w in validation)]
        remaining = residual(validation, self.panel)
        return {'panel': list(self.panel), 'monitor_tests': tests,
                'identical_outputs_in_sample': exact_matches,
                'unselected': [n for n in names if n not in self.panel],
                'residual_target_bits': remaining,
                'missing_target_information_alert': remaining > self.tolerance,
                'all_selected_contributions_detected': bool(tests) and all(
                    r['distinct_contribution_detected'] for r in tests.values()),
                'n_validation': len(validation)}


def experiment(seed=0):
    auditor = MetaWatcher().fit(generate(2 * seed))
    normal = auditor.audit(generate(2 * seed + 1))
    failed = auditor.audit(generate(2 * seed + 1, mode='copy_failure'))
    xor_auditor = MetaWatcher().fit(generate(2 * seed, mode='xor'))
    xor = xor_auditor.audit(generate(2 * seed + 1, mode='xor'))
    return {'seed': seed, 'normal': normal, 'copy_failure': failed, 'xor': xor}


if __name__ == '__main__':
    print(json.dumps({'protocol': {'discovery_n': 1024, 'validation_n': 1024,
          'permutations': 999, 'family_alpha_per_audit': 0.05,
          'minimum_gain_bits': 0.05, 'selection_tolerance_bits': 0.01,
          'seeds_fixed_before_run': list(range(5)),
          'scope': 'synthetic categorical IID; no automatic deletion'},
          'runs': [experiment(s) for s in range(5)]}, indent=2))
