import math

# Fault prior
pT = {1: 0.10, 0: 0.90}

# Primary detector: sensitivity 0.80, false-alarm rate 0.10
pW1_T = {1: {1: 0.80, 0: 0.20},
         0: {1: 0.10, 0: 0.90}}

# Design B drift monitor: conditionally independent of W1 given T
pW2_T = {1: {1: 0.60, 0: 0.40},
         0: {1: 0.05, 0: 0.95}}

joint = {(t, w1, w2): pT[t] * pW1_T[t][w1] * pW2_T[t][w2]
         for t in (0, 1) for w1 in (0, 1) for w2 in (0, 1)}

def marginal(idx):
    d = {}
    for k, v in joint.items():
        kk = tuple(k[i] for i in idx)
        d[kk] = d.get(kk, 0.0) + v
    return d

pW1, pW1W2, pTW1 = marginal([1]), marginal([1, 2]), marginal([0, 1])

# I(T ; W2 | W1)
cmi = sum(p * math.log2((p * pW1[(w1,)]) / (pTW1[(t, w1)] * pW1W2[(w1, w2)]))
          for (t, w1, w2), p in joint.items() if p > 0)

# I(T ; W1)
mi = sum(p * math.log2(p / (pT[t] * pW1[(w1,)]))
         for (t, w1), p in pTW1.items() if p > 0)

H = -sum(p * math.log2(p) for p in pT.values())

print(f"H(T)         = {H:.4f} bits")
print(f"I(T;W1)      = {mi:.4f} bits")
print(f"H(T|W1)      = {H - mi:.4f} bits")
print(f"I(T;W2|W1)   = {cmi:.4f} bits   (Design B)")
print(f"residual     = {100 * cmi / (H - mi):.1f}% of what W1 left")
