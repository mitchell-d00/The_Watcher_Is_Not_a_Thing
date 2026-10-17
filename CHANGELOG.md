# Revision history

## 2026-10-17 — Bounded meta-watcher stopping experiment (revision 2)

- Added fixed-sample simultaneous information-gain intervals with an explicit
  finite-alphabet derivation and predeclared practical minimum.
- Added continue, bounded-stop, and inconclusive outcomes; incomplete subset
  searches cannot certify a stop. No non-significance-to-absence inference.
- Recorded five seeds across four scenarios and added 10 stopping tests.
- Brought revision-1 experiment into main while retaining its branch and results.
- Added README and validation addenda. Original paper versions remain unchanged.
- Still open: real-world validation, sequential monitoring, high-dimensional
  estimation, and the paper's state-definition/log-loss/causal-vocabulary issues.

## 2026-10-17 — Meta-watcher experiment (revision 1)

Commit `d2ed69c909b23db4d76c3f321bb9132931149d6b`, branch
`experiment/watcher-audit-2026-10-17`.

- Added an auditor of monitor outputs with separate discovery and validation.
- Searched combinations to retain XOR synergy; detected injected copying failure.
- Added 7 tests and five-seed results. Empirical residual alerts were heuristic;
  this version did not establish a statistical stopping certificate.

## Earlier code validation

Base commit `30b988ec22868fdc42fe6bea506535fb7dd1cee9`.
The 12-test permutation implementation and original reproduction record remain
in VALIDATION.md. Paper withdrawals and corrections remain in its Appendix B.
