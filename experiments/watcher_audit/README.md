# A watcher that audits other watchers

This is a synthetic, executable experiment built on the repository's existing
categorical permutation test. It operationalizes separate work as information
about a declared target that the other selected monitors do not already supply.
Different output strings alone do not qualify as different work.

## Architecture

Two independent fair bits A and B define the target (A,B). Five first-level
monitors emit A, a copy of A, B, independent noise, and a constant respectively.
The meta-watcher receives their logged outputs and delayed ground-truth labels.
It selects a smallest panel on discovery data, freezes that panel, then tests
each member's conditional information on independent validation observations.
The audit is a report and alert, not an automatic deletion mechanism.

Panel selection searches all subsets, comparing empirical residual target
entropy to that of the complete panel, with a 0.01-bit tolerance. This avoids
discarding complementary monitors just because they are individually
uninformative. There is a hard limit of 10 candidate monitors because search
cost grows exponentially. Equal-size ties favor lower empirical residual
entropy, then input order. A copied monitor could be chosen as representative;
the rule does not assert which physical monitor is the original.

## Fixed protocol

- Five seeds: 0 through 4, chosen before execution.
- 1,024 discovery observations and 1,024 independent validation observations.
- 999 within-stratum permutations per selected monitor.
- Bonferroni correction within each audit: family alpha 0.05.
- Minimum detected contribution: 0.05 bits.
- Fixed selected panel is also evaluated after B's monitor is changed to copy A.
- Separate XOR scenario: target A XOR B, outputs A and B. Both are needed.
- Failure and normal scenarios intentionally use paired underlying random draws.

## Reproduce from repository root

```bash
python3 experiments/watcher_audit/audit.py
python3 -m unittest discover -s experiments/watcher_audit -v
python3 -m unittest discover -s tests -v
```

Only the Python standard library is required. No network calls or external data.
The script prints JSON; results.json records the initial complete run.

## Observed results

All five runs selected watch_a and watch_b, leaving the duplicate, noise, and
stuck monitor unselected. Each selected monitor contributed 0.9966 to 0.9998
bits conditional on the other, p=0.001; residual target entropy was zero.

When watch_b copied watch_a, the frozen panel lost its distinct contributions
and an alert reported approximately one missing bit (0.9966 to 0.9998).
Both monitors remain in the report; the auditor does not delete both merely
because each is redundant relative to its copy. It cannot decide which is faulty
from duplicate outputs alone. The target residual detects lost coverage.

All XOR runs retained both monitors, detected their conditional contributions,
and left zero empirical residual target entropy. The exact balanced XOR test
also verifies that either monitor alone leaves one full bit unresolved.

Seven experiment tests and all twelve original repository tests passed.

## What this establishes and what remains open

This demonstrates a working meta-monitor on small synthetic categorical data.
It does not certify that monitors perform distinct physical computations,
measure causal usefulness, or establish the paper's general stopping rule.
Ground-truth target labels are essential; the auditor cannot verify its own
truth source. No real system or language-model agents were used.

Empirical zero residual entropy and identical observed outputs are sample
findings, not population equivalence proofs. The simulation's construction
supplies known ground truth. No-power/no-gain results are not proof of zero.
The entropy-based alert is heuristic and has no calibrated false-alert rate.
The experiment does not validate rare-event behavior, noisy target labels,
continuous states, serial dependence, or sparse high-dimensional strata.
Bonferroni correction covers one audit only, not indefinite repeated monitoring.
There is no claim that five seeds quantify general reliability. Deployment
would require an independent validation protocol and sequential error control.

Source base: 30b988ec22868fdc42fe6bea506535fb7dd1cee9.
The original paper and implementation are unchanged.
