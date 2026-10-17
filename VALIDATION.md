# Reproduction and permutation-test implementation

## Addendum: 17 October 2026

The historical validation record below is retained. The new experiment adds
7 meta-watcher tests and 10 bounded-stopping tests; all 29 tests including the
original 12 passed. Full output is recorded in
`experiments/watcher_audit/verification.txt`.

Five fixed seeds each reproduce panel selection, copying-failure detection,
and XOR retention in `results.json`. The separate `stopping_results.json`
records 20 audits: five each for redundant candidates, independent irrelevant
candidates with unresolved target uncertainty, XOR, and small-sample XOR.
Both large-sample null scenarios stop within scope, large-sample XOR continues,
and small-sample XOR remains inconclusive in every run.

The stopping certificate is a separate fixed-sample method with predeclared
finite supports, not a new interpretation of a non-significant permutation test.
Its derivation, assumptions, conservative sample requirements, and remaining
limits are in [STOPPING.md](experiments/watcher_audit/STOPPING.md).
Original paper files and scripts are retained unchanged.

## What was checked

The original code at `09bebc11674027d9e3ee9b12b981919018ccc2ad` ran successfully with Python 3.12.
`watcher_gate.py` reproduced the §11 values, including 0.0791 bits and 25.9%
of residual uncertainty. `estimation.py` reproduced all three reported tables,
including the N=100 noise 95th percentile of 0.0427 bits and regime shares
from 0.1% to 54.8%. Those two source files were not modified.

No blank README files existed in the tracked repository. No meaningful README
content was removed. Local Python caches are now excluded from version control.

## The implementation gap addressed

The original finite-sample simulation samples from a known screened-off joint
distribution. It does not perform the paper's proposed permutation test on an
observed sample. `permutation_gate.py` now supplies that test for categorical
observations `(T, W1, W2)`. It is a statistical component, not a complete Gate
with power, practical-effect thresholds, boundary validation and termination.

W2 is shuffled independently within each W1 stratum, preserving the observed
(T,W1) and (W1,W2) margins. Conditional mutual information is recomputed for
each of B random shuffles. The reported upper quantile uses nearest rank.
The Monte Carlo upper-tail p-value is `(1 + count(null >= observed))/(B + 1)`;
ties are counted conservatively with a numerical tolerance of 1e-12 bits.
It never reports a sampled p-value of zero.

The normalized gain and normalized null quantile both divide by the observed
H(T|W1), which these shuffles preserve. Admission-sized evidence must clear
both the sampled upper quantile and the declared alpha. A statistically resolved
gain is not automatically a practically worthwhile gain.

The method follows categorical within-group permutation as discussed in
[Berrett et al., Conditional Permutation Test](https://academic.oup.com/jrsssb/article/82/1/175/7056014)
and the nonzero Monte Carlo p-value treatment of
[Phipson and Smyth](https://pubmed.ncbi.nlm.nih.gov/21044043/).

## Recorded demonstrations

Parameters were fixed to N=1000, B=999, sample seed 0, permutation seed 1,
alpha 0.05; no seeds or thresholds were searched to obtain these outcomes.

| Synthetic sample | Estimated CMI, bits | Null 95th percentile, bits | Monte Carlo p | Status |
|---|---:|---:|---:|---|
| Design B | 0.050991 | 0.003956 | 0.001 | gain_resolved |
| Screened-off layer | 0.000755 | 0.004313 | 0.641 | no_gain_resolved |

Design B's sample estimate differs from its population value of 0.0791 bits.
That difference is sampling variability, not a correction to the worked example.
The screened-off demonstration does not establish zero gain by its p-value;
zero population gain is known from that synthetic generator's construction.
Neither demonstration validates the philosophical claims or real-world utility.

## Checks and reproduction

All **12 standard-library tests passed**. They include known entropy/CMI cases,
stratum-margin preservation, a Monte Carlo comparison against an exhaustively
enumerated four-row null with exact upper-tail probability 1/3, conservative
ties, positive p-values, undefined normalization, input validation, seed
reproducibility, CSV declaration requirements and original-script regression.

```bash
python3 -m unittest discover -s tests -v
python3 watcher_gate.py
python3 estimation.py
python3 permutation_gate.py --demo design-b --out results/permutation-design-b.json
python3 permutation_gate.py --demo screened-off --out results/permutation-screened-off.json
```

For an observed categorical sample with header exactly `T,W1,W2`:

```bash
python3 permutation_gate.py --csv observations.csv \
  --target 'predeclared target' --boundary 'predeclared boundary' \
  --ordering 'predeclared lower-to-upper ordering' \
  --regime 'predeclared operating regime' \
  --alpha 0.05 --permutations 999 --seed 1 --out result.json
```

CSV labels are treated as categories, not continuous numbers. In the Python API,
a tuple-valued W1 can encode the joint state of all lower layers. The CSV CLI
expects that joint state to have been encoded as one categorical field.

## Limits left open

- Inference assumes independent observations and exchangeability under the
  conditional-independence null within each lower-state stratum. This implementation
  is not valid for arbitrary time-series, clustered or continuous conditioning data.
- Many sparse strata can make power poor. Stratum and singleton counts are
  reported, but this tool does not certify sample adequacy or choose a binning rule.
- No residual target uncertainty or no stratum with target and W2 variation
  returns `could_not_run`, with no p-value and no termination verdict.
- `no_gain_resolved` is an unresolved statistical result, not proof of absence.
  No minimum-effect equivalence test or power study has been implemented.
- Alpha, target, boundary, ordering, regime and any practical minimum gain must
  be chosen before inspecting the sample. Supplying text to the CLI cannot
  establish that this happened or that the boundary is appropriate.
- Repeated testing of layers or searching regimes needs a declared multiple-test
  procedure. This single-layer tool does not implement one.
- The existing paper PDF, Markdown and plain-text source remain unchanged.
  This implementation does not resolve its prior-art or philosophical kill conditions.
