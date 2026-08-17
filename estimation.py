import math, random

def cmi_from_joint(joint):
    """I(T;W2|W1) from a joint dict over (t,w1,w2)."""
    def marg(idx):
        d = {}
        for k, v in joint.items():
            kk = tuple(k[i] for i in idx)
            d[kk] = d.get(kk, 0.0) + v
        return d
    pW1, pW1W2, pTW1 = marg([1]), marg([1, 2]), marg([0, 1])
    tot = 0.0
    for (t, w1, w2), p in joint.items():
        if p <= 0: continue
        num = p * pW1[(w1,)]
        den = pTW1[(t, w1)] * pW1W2[(w1, w2)]
        if den <= 0: continue
        tot += p * math.log2(num / den)
    return tot

def build(pT1, sens, fpr, b1, b0):
    pT = {1: pT1, 0: 1 - pT1}
    pW1 = {1: {1: sens, 0: 1 - sens}, 0: {1: fpr, 0: 1 - fpr}}
    pW2 = {1: {1: b1, 0: 1 - b1}, 0: {1: b0, 0: 1 - b0}}
    return {(t, w1, w2): pT[t] * pW1[t][w1] * pW2[t][w2]
            for t in (0, 1) for w1 in (0, 1) for w2 in (0, 1)}

def H(pT1):
    return -sum(p * math.log2(p) for p in (pT1, 1 - pT1) if p > 0)

def residual(joint, pT1):
    def marg(idx):
        d = {}
        for k, v in joint.items():
            kk = tuple(k[i] for i in idx)
            d[kk] = d.get(kk, 0.0) + v
        return d
    pTW1, pW1 = marg([0, 1]), marg([1])
    pT = {1: pT1, 0: 1 - pT1}
    mi = sum(p * math.log2(p / (pT[t] * pW1[(w1,)]))
             for (t, w1), p in pTW1.items() if p > 0)
    return H(pT1) - mi

# ---------- 1. FINITE-SAMPLE BIAS FLOOR (true CMI = 0) ----------
# Design A: W2 is a deterministic function of W1, so true I(T;W2|W1) = 0 exactly.
# But W2=f(W1) makes the plug-in degenerate; use the harder honest case:
# W2 depends ONLY on W1 stochastically (still screened off, true CMI = 0).
print("=" * 62)
print("1. FINITE-SAMPLE BIAS: a screened-off layer, true CMI = 0")
print("=" * 62)

pT1, sens, fpr = 0.10, 0.80, 0.10
pW2_given_W1 = {1: 0.70, 0: 0.20}   # depends on W1 only -> screened off

pT = {1: pT1, 0: 1 - pT1}
pW1c = {1: {1: sens, 0: 1 - sens}, 0: {1: fpr, 0: 1 - fpr}}
true_joint = {(t, w1, w2): pT[t] * pW1c[t][w1] *
              (pW2_given_W1[w1] if w2 == 1 else 1 - pW2_given_W1[w1])
              for t in (0, 1) for w1 in (0, 1) for w2 in (0, 1)}
print(f"true I(T;W2|W1) = {cmi_from_joint(true_joint):.6f} bits")

cells = list(true_joint.items())
rng = random.Random(0)

def sample_cmi(N):
    r = rng.random
    cum, acc = [], 0.0
    for k, p in cells:
        acc += p
        cum.append((acc, k))
    counts = {}
    for _ in range(N):
        u = r()
        for c, k in cum:
            if u <= c:
                counts[k] = counts.get(k, 0) + 1
                break
    return cmi_from_joint({k: v / N for k, v in counts.items()})

for N in (100, 500, 1000, 5000, 20000):
    trials = sorted(sample_cmi(N) for _ in range(400))
    mean = sum(trials) / len(trials)
    p95 = trials[int(0.95 * len(trials))]
    print(f"  N={N:>6}   mean estimate = {mean:.4f} bits   95th pct = {p95:.4f} bits")

# ---------- 2. REGIME DEPENDENCE ----------
print()
print("=" * 62)
print("2. REGIME DEPENDENCE: Design B under different drift prevalence")
print("=" * 62)
print("  b1 = P(flag | fault), b0 = P(flag | no fault)")
for b1, b0, label in [(0.12, 0.10, "nominal, drift rare"),
                      (0.25, 0.12, "mild drift"),
                      (0.60, 0.05, "the paper's example"),
                      (0.85, 0.03, "heavy drift")]:
    j = build(0.10, 0.80, 0.10, b1, b0)
    d = cmi_from_joint(j)
    res = residual(j, 0.10)
    print(f"  {label:<22} b1={b1:.2f} b0={b0:.2f}  "
          f"dD={d:.4f} bits  = {100*d/res:5.1f}% of residual")

# ---------- 3. BASE-RATE DEPENDENCE ----------
print()
print("=" * 62)
print("3. BASE-RATE DEPENDENCE: same architecture, different prior")
print("=" * 62)
for pt in (0.50, 0.20, 0.10, 0.02, 0.005):
    j = build(pt, 0.80, 0.10, 0.60, 0.05)
    d = cmi_from_joint(j)
    res = residual(j, pt)
    print(f"  P(T=1)={pt:<6} H(T)={H(pt):.4f}  dD={d:.4f} bits  "
          f"= {100*d/res:5.1f}% of residual")
