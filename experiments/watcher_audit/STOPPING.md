# Bounded stopping: revision 2

Date: 17 October 2026. This supplements, rather than silently rewrites, the
paper and the initial meta-watcher experiment.

## The question answered

Given a frozen baseline B, declared target T, finite candidate monitors C,
and a practical minimum delta, does any candidate combination add more than
delta bits of information about T conditional on B?

The output is:

- `continue`: at least one combination's lower confidence bound exceeds delta.
- `stop_within_declared_scope`: every combination's upper bound is at most delta,
  and all combinations in the declared candidate set were searched.
- `inconclusive`: neither has been established, including incomplete searches.

This is an absolute-bit practical-equivalence criterion. It is not the paper's
normalized threshold and must not be represented as an implementation of every
part of the paper's Gate. The user must justify delta for the declared target.
Stopping does not assert zero gain, uselessness, or permanent global termination.

## Confidence construction

Let the full declared joint alphabet of (T,B,C) have size K and let n independent,
identically distributed observations define empirical distribution P_hat.
All possible cells, including unobserved cells, count toward K.

Total variation is the maximum of P_hat(A)-P(A) over subsets A of the alphabet.
For any fixed A, the one-sided Hoeffding bound is exp(-2 n r^2). Union bounding
over at most 2^K events gives a simultaneous radius

    r = min(1, sqrt((K ln(2) + ln(1/alpha)) / (2 n))).

With probability at least 1-alpha, every marginal is also within r in total
variation. For a marginal with k states, its entropy error in bits is bounded by

    f(r,k) = h2(d) + d log2(k-1), d = min(r, 1-1/k),

with f(r,1)=0. The cap handles the fact that this expression is not increasing
beyond 1-1/k. This is the classical finite-alphabet entropy continuity bound;
see [Audenaert, 2007](https://arxiv.org/abs/quant-ph/0610146).

For each candidate group G, expand

    I(T;G | B) = H(T,B) + H(B,G) - H(B) - H(T,B,G).

Sum the four corresponding f terms to obtain error E. Clip the interval
[I_hat-E, I_hat+E] to [0, min(log2 |T|, log2 |G|)]. All these intervals share
the same full-joint confidence event: the 1-alpha statement covers all searched
groups simultaneously, not separately. No independence between candidate
monitors is assumed. No additional candidate-wise Bonferroni factor is needed.

This provides a finite-sample bound under the stated assumptions; the code and
derivation remain open to independent review. Tests are not a proof of coverage.

## Input contract and relation to the first experiment

`certify(counts, alphabet_sizes, minimum_bits=0.25, alpha=0.05)` takes a count
table keyed by integer tuples `(target, baseline, candidate_0, ...)` and fixed
alphabet sizes in that order. A joint selected panel can be encoded as the
baseline categorical state using a mapping fixed before the audit. Preserve
the full declared support; do not infer alphabet size from observed values.

Fit/select on discovery data, freeze that representation and the candidate
universe, then collect a NEW fixed-size audit sample. Ground-truth target labels
must be available. Counts must correspond to IID observations, not arbitrary
repeated copies or correlated time-series. The function checks encoding and
counts; it cannot verify IID sampling, prior declaration, or truthfulness.

All combinations of up to 10 candidate monitors are supported. `max_group`
can restrict computation, but partial searches return inconclusive unless a
tested combination already warrants continue. Merely checking singletons
cannot certify a stop for a larger declared candidate universe.

## Reproduction and initial findings

```bash
python3 experiments/watcher_audit/stopping.py
python3 -m unittest discover -s experiments/watcher_audit -v
python3 -m unittest discover -s tests -v
```

The protocol was fixed before execution: seeds 0 through 4, alpha=0.05 per
audit, delta=0.25 bits, 250,000 observations for large samples and 32 for small.
All candidate definitions and supports are fixed in the generator.

| Scenario | Outcome in all five runs |
| --- | --- |
| Baseline knows T; candidates copy it or add noise | Stop within scope |
| Baseline empty; both candidates independent of unsolved T | Stop within scope |
| Baseline empty; candidates A,B; T=A XOR B | Continue because the pair helps |
| Same XOR scenario with 32 observations | Inconclusive |

See `stopping_results.json` for every interval and verdict. These 20 runs are
demonstrations, not a claim of 95% simultaneous confidence across all runs.
The original 12 tests, 7 meta-watcher tests, and 10 stopping tests pass.

## Limits and historical corrections

The original paper's first-small-increment stopping rule does not protect
against later synergistic inputs. Revision 1 searched combinations but supplied
no evidence-of-absence guarantee. Revision 2 adds the bounded certificate;
it does not retroactively turn revision-1 entropy heuristics into confidence bounds.

The guarantee is confined to the declared candidates, target, baseline, support,
and stationary regime. It cannot exclude a future unlisted sensor or changed
environment. Large supports make the bound conservative or uninformative;
exhaustive search is exponential. Failure to resolve is an expected result.

This is fixed-sample inference, NOT a confidence sequence. Do not keep sampling
until it says stop or repeatedly reuse alpha=0.05 in deployment. Repeated checks
need a prespecified alpha-spending schedule and valid sampling, or a separately
proved sequential method. No such scheduler is implemented here.

No claim about consciousness, causal usefulness, operational deletion, or
novelty relative to causal modeling follows. The historical state-definition
and fitted-log-loss claims remain to be revised in the paper itself. Its PDF,
Markdown, and text are preserved as historical versions, not silently repaired.
