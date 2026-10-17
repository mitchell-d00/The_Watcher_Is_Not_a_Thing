"""Finite-alphabet, fixed-sample simultaneous CMI stopping certificate.

Input counts represent IID held-out observations (target, baseline, candidates).
Alphabet sizes and candidate set must be fixed before seeing these observations.
"""
import itertools
import json
import math
import random
from collections import Counter


def entropy(counts):
    total = sum(counts.values())
    return -sum(c / total * math.log2(c / total) for c in counts.values() if c)


def continuity(radius, alphabet):
    if alphabet == 1:
        return 0.0
    d = min(radius, 1 - 1 / alphabet)
    binary = -sum(p * math.log2(p) for p in (d, 1-d) if p)
    return binary + d * math.log2(alphabet - 1)


def certify(counts, alphabet_sizes, *, minimum_bits=0.25, alpha=0.05,
            max_group=None):
    """Return stop/continue/inconclusive; never equate nonsignificance to stop.

    All subsets share one confidence event on the full joint distribution.
    max_group limits search; a partial search cannot issue a stop certificate.
    No optional stopping or reuse of this alpha across repeated looks is allowed.
    """
    sizes = tuple(alphabet_sizes)
    if len(sizes) < 3 or any(type(s) is not int or s < 1 for s in sizes):
        raise ValueError('declare positive integer alphabets for target, baseline, candidates')
    if not 0 < alpha < 1 or not math.isfinite(minimum_bits) or minimum_bits <= 0:
        raise ValueError('invalid alpha or practical minimum')
    if not counts:
        raise ValueError('empty sample')
    for row, count in counts.items():
        if len(row) != len(sizes) or type(count) is not int or count < 0:
            raise ValueError('invalid count table')
        if any(type(x) is not int or not 0 <= x < k for x, k in zip(row, sizes)):
            raise ValueError('observation outside predeclared support')
    n = sum(counts.values())
    if n < 1:
        raise ValueError('empty sample')
    candidates = len(sizes) - 2
    if candidates > 10:
        raise ValueError('experiment supports at most 10 candidate monitors')
    limit = candidates if max_group is None else max_group
    if type(limit) is not int or not 1 <= limit <= candidates:
        raise ValueError('invalid search limit')
    k = math.prod(sizes)
    # TV = max over events of empirical minus true probability. Hoeffding
    # for each of <=2**K events, then union bound. No occupied-cell shortcut.
    radius = min(1.0, math.sqrt((k * math.log(2) + math.log(1/alpha)) / (2*n)))

    def h(indices):
        marginal = Counter()
        for row, count in counts.items():
            marginal[tuple(row[i] for i in indices)] += count
        return entropy(marginal)

    reports = []
    for width in range(1, limit + 1):
        for group in itertools.combinations(range(2, len(sizes)), width):
            terms = [(0, 1), (1,) + group, (1,), (0, 1) + group]
            estimates = [h(t) for t in terms]
            estimate = max(0.0, estimates[0] + estimates[1] - estimates[2] - estimates[3])
            error = sum(continuity(radius, math.prod(sizes[i] for i in t)) for t in terms)
            cap = min(math.log2(sizes[0]), math.log2(math.prod(sizes[i] for i in group)))
            lower, upper = max(0.0, estimate-error), min(cap, estimate+error)
            reports.append({'candidate_indices': [i-2 for i in group],
                            'estimate_bits': estimate, 'lower_bits': lower,
                            'upper_bits': upper})
    complete = limit == candidates
    if any(r['lower_bits'] > minimum_bits for r in reports):
        status = 'continue'
    elif complete and all(r['upper_bits'] <= minimum_bits for r in reports):
        status = 'stop_within_declared_scope'
    else:
        status = 'inconclusive'
    return {'status': status, 'n': n, 'alpha': alpha,
            'minimum_bits': minimum_bits, 'joint_alphabet_size': k,
            'tv_radius': radius, 'complete_subset_search': complete,
            'groups': reports}


def sample(mode, n, seed):
    rng = random.Random(seed)
    counts = Counter()
    for _ in range(n):
        a, b, c = rng.randrange(2), rng.randrange(2), rng.randrange(2)
        if mode == 'redundant':
            row = (a, a, a, b)
        elif mode == 'xor':
            row = (a ^ b, 0, a, b)
        elif mode == 'independent_null':
            row = (a, 0, b, c)
        else:
            raise ValueError('unknown mode')
        counts[row] += 1
    return counts, (2, 2 if mode == 'redundant' else 1, 2, 2)


if __name__ == '__main__':
    output = {'protocol': {'seeds': list(range(5)), 'large_n': 250000,
              'small_n': 32, 'minimum_bits': 0.25, 'alpha_per_fixed_audit': 0.05,
              'candidate_order': ['A', 'B'],
              'note': 'five demonstrations; no pooled or sequential confidence claim'}, 'runs': []}
    for seed in range(5):
        for mode, n in [('redundant', 250000), ('independent_null', 250000),
                        ('xor', 250000), ('xor', 32)]:
            counts, sizes = sample(mode, n, seed)
            output['runs'].append({'seed': seed, 'scenario': mode,
                                   **certify(counts, sizes)})
    print(json.dumps(output, indent=2))
