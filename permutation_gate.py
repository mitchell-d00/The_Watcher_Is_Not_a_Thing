"""Discrete, within-stratum permutation test; no third-party dependencies.

Rows are (T, W1, W2). A tuple-valued W1 may encode all lower layers.
Valid inference requires independent rows, exchangeability within W1 strata,
and declarations made before observing results. This is not a test of causality.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random


def validate_rows(rows):
    rows = list(rows)
    if not rows:
        raise ValueError('at least one observation is required')
    for row in rows:
        if len(row) != 3:
            raise ValueError('each observation must contain T, W1, W2')
        for value in row:
            if value is None or value == '' or (isinstance(value, float) and not math.isfinite(value)):
                raise ValueError('missing or nonfinite labels are not supported')
            hash(value)
    return [tuple(row) for row in rows]


def information(rows):
    """Return plug-in CMI and conditional target entropy, in bits."""
    n = len(rows)
    joint = Counter(rows)
    w1 = Counter(b for a, b, c in rows)
    tw1 = Counter((a, b) for a, b, c in rows)
    w1w2 = Counter((b, c) for a, b, c in rows)
    cmi = math.fsum(count / n * math.log2(count * w1[b] / (tw1[a, b] * w1w2[b, c]))
                    for (a, b, c), count in joint.items())
    entropy = -math.fsum(count / n * math.log2(count / w1[b])
                        for (a, b), count in tw1.items())
    return max(0.0, cmi), max(0.0, entropy)


def permute_within_strata(rows, rng):
    groups = defaultdict(list)
    for i, (_, lower, _) in enumerate(rows):
        groups[lower].append(i)
    shuffled = list(rows)
    for indexes in groups.values():
        values = [rows[i][2] for i in indexes]
        rng.shuffle(values)
        for i, value in zip(indexes, values):
            shuffled[i] = (rows[i][0], rows[i][1], value)
    return shuffled


def permutation_test(rows, *, permutations=999, alpha=0.05, seed=0):
    rows = validate_rows(rows)
    if not 0 < alpha < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    if isinstance(permutations, bool) or not isinstance(permutations, int) or permutations < 1:
        raise ValueError('permutations must be a positive integer')
    if 1 / (permutations + 1) > alpha:
        raise ValueError('too few permutations to resolve the requested alpha')
    observed, entropy = information(rows)
    groups = defaultdict(list)
    for row in rows:
        groups[row[1]].append(row)
    informative = sum(len({r[0] for r in group}) > 1 and len({r[2] for r in group}) > 1
                      for group in groups.values())
    result = dict(n=len(rows), n_strata=len(groups), informative_strata=informative,
                  singleton_strata=sum(len(g) == 1 for g in groups.values()),
                  observed_cmi_bits=observed, residual_entropy_bits=entropy,
                  normalized_gain=observed / entropy if entropy > 0 else None,
                  alpha=alpha, permutations=permutations, seed=seed,
                  null_quantile_bits=None, normalized_null_quantile=None,
                  monte_carlo_p=None, status='could_not_run')
    if entropy == 0 or informative == 0:
        result['reason'] = 'No residual target uncertainty or no stratum with both target and layer variation.'
        return result
    rng = random.Random(seed)
    null = sorted(information(permute_within_strata(rows, rng))[0]
                  for _ in range(permutations))
    # Nearest-rank upper quantile; ties count as at least as extreme.
    floor = null[math.ceil((1 - alpha) * permutations) - 1]
    extreme = sum(value >= observed - 1e-12 for value in null)
    p = (extreme + 1) / (permutations + 1)
    result.update(null_quantile_bits=floor, normalized_null_quantile=floor / entropy,
                  monte_carlo_p=p,
                  status='gain_resolved' if p <= alpha and observed > floor + 1e-12 else 'no_gain_resolved')
    result['reason'] = ('Clears the sampled null under the declared assumptions; not an effect-size or usefulness verdict.'
                        if result['status'] == 'gain_resolved' else
                        'Does not clear the sampled null; not evidence of zero gain or a termination verdict. Power has not been established.')
    return result


def demo_rows(kind, n, seed):
    if n < 1:
        raise ValueError('samples must be positive')
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        t = int(rng.random() < 0.10)
        w1 = int(rng.random() < (0.80 if t else 0.10))
        probability = (0.60 if t else 0.05) if kind == 'design-b' else (0.70 if w1 else 0.20)
        rows.append((t, w1, int(rng.random() < probability)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--demo', choices=['design-b', 'screened-off'])
    source.add_argument('--csv', type=Path, help='categorical observations with exactly T,W1,W2 headers')
    ap.add_argument('--samples', type=int, default=1000, help='demo sample size')
    ap.add_argument('--sample-seed', type=int, default=0)
    ap.add_argument('--seed', type=int, default=1, help='permutation seed')
    ap.add_argument('--permutations', type=int, default=999)
    ap.add_argument('--alpha', type=float, default=0.05)
    for name in ['target', 'boundary', 'ordering', 'regime']:
        ap.add_argument('--' + name)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    try:
        if args.demo:
            rows = demo_rows(args.demo, args.samples, args.sample_seed)
            declarations = dict(target='synthetic binary fault T', boundary='two synthetic binary monitor outputs',
                                ordering='W1 below W2; conditioning on W1',
                                regime=args.demo + ': parameters fixed in demo_rows; IID simulated observations')
        else:
            declarations = {name: getattr(args, name) for name in ['target', 'boundary', 'ordering', 'regime']}
            if not all(v and v.strip() for v in declarations.values()):
                ap.error('CSV runs require --target, --boundary, --ordering and --regime declared before analysis')
            with args.csv.open(newline='') as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames != ['T', 'W1', 'W2']:
                    ap.error('CSV header must be exactly T,W1,W2')
                rows = []
                for row in reader:
                    if None in row:
                        raise ValueError('CSV contains extra columns')
                    rows.append((row['T'], row['W1'], row['W2']))
        result = permutation_test(rows, permutations=args.permutations, alpha=args.alpha, seed=args.seed)
        result.update(declarations=declarations, synthetic=bool(args.demo),
                      sample_sha256=hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest(),
                      sample_seed=args.sample_seed if args.demo else None,
                      notice='Discrete IID/exchangeable rows only. Labels and declarations do not prove these assumptions. No power or equivalence analysis; no structural termination verdict.')
        output = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output)
        print(output, end='')
    except (ValueError, TypeError, OSError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
