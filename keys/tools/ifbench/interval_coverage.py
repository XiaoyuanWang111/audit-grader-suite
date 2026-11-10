"""Coverage of 95% intervals for a stratified error rate, by simulation.

Each simulated review draws n_h cases without replacement from stratum h, which holds N_h verdicts of which a known
share are errors. The estimate is the stratum-size-weighted error share. Interval rules compared:
  boot       percentile bootstrap that resamples cases within strata (the rule in the audit-grader skill as merged)
  boot+sum   boot, upper end raised by weight x exact zero-error limit for every stratum whose sample has no error
  boot+max   boot, upper end raised once, by the largest such product
  jeffreys   Monte Carlo over independent Beta(e + 1/2, n - e + 1/2) draws per stratum
  uniform    the same with Beta(e + 1, n - e + 1)
  exact-sum  weighted sum of the strata's Clopper-Pearson limits
Prints, per scenario and rule: coverage of the true rate, how often the truth lies above the upper end and below the
lower end, and the mean lower and upper ends. The scenarios use the stratum shapes of the earlier IFBench audit's two
review rounds and, without a replacement grader, one stratum per label. Needs numpy and scipy.

Usage: python -B keys/tools/ifbench/interval_coverage.py
"""

import sys

import numpy as np
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
DATASETS = 4000
REPLICATES = 2000
SEED = 10060


def run(name, pops, ns, rates):
    rng = np.random.default_rng(SEED)
    pops = np.array(pops)
    ns = np.array(ns)
    weights = pops / pops.sum()
    errors_pop = np.array([round(n * p) for n, p in zip(pops, rates, strict=False)])
    truth = errors_pop.sum() / pops.sum()
    x = np.stack(
        [rng.hypergeometric(k, n_pop - k, n, size=DATASETS) for k, n_pop, n in zip(errors_pop, pops, ns, strict=False)],
        axis=1,
    )
    point = (weights * x / ns).sum(axis=1)

    boot = np.zeros((DATASETS, REPLICATES))
    jeff = np.zeros((DATASETS, REPLICATES))
    unif = np.zeros((DATASETS, REPLICATES))
    for h in range(len(pops)):
        xh = x[:, h][:, None]
        boot += weights[h] * rng.binomial(ns[h], xh / ns[h], size=(DATASETS, REPLICATES)) / ns[h]
        jeff += weights[h] * rng.beta(xh + 0.5, ns[h] - xh + 0.5, size=(DATASETS, REPLICATES))
        unif += weights[h] * rng.beta(xh + 1.0, ns[h] - xh + 1.0, size=(DATASETS, REPLICATES))
    intervals = {}
    low, high = np.percentile(boot, [2.5, 97.5], axis=1)
    intervals["boot"] = (low, high)
    zero_limit = weights * (1 - 0.025 ** (1 / ns)) * (x == 0)
    intervals["boot+sum"] = (low, high + zero_limit.sum(axis=1))
    intervals["boot+max"] = (low, high + zero_limit.max(axis=1))
    intervals["jeffreys"] = tuple(np.percentile(jeff, [2.5, 97.5], axis=1))
    intervals["uniform"] = tuple(np.percentile(unif, [2.5, 97.5], axis=1))
    cp_low = np.where(x == 0, 0.0, stats.beta.ppf(0.025, x, ns - x + 1))
    cp_high = np.where(x == ns, 1.0, stats.beta.ppf(0.975, x + 1, ns - x))
    intervals["exact-sum"] = ((weights * cp_low).sum(axis=1), (weights * cp_high).sum(axis=1))

    zero_share = (x == 0).mean(axis=0)
    print(
        f"\n{name}: populations {pops.tolist()}, sampled {ns.tolist()}, "
        f"true stratum rates {[round(k / n, 4) for k, n in zip(errors_pop, pops, strict=False)]}, "
        f"true rate {100 * truth:.2f}%, mean estimate {100 * point.mean():.2f}%, "
        f"share of reviews with a zero-error stratum {np.round(zero_share, 2).tolist()}"
    )
    for rule, (low, high) in intervals.items():
        above = (truth > high + 1e-12).mean()
        below = (truth < low - 1e-12).mean()
        print(
            f"   {rule:10s} coverage {100 * (1 - above - below):5.1f}%   truth above {100 * above:4.1f}%   "
            f"below {100 * below:4.1f}%   mean interval [{100 * low.mean():.2f}, {100 * high.mean():.2f}]"
        )


# With a replacement grader: the shapes of the IFBench audit's two rounds (disagreement stratum, agreement stratum).
for agree_rate in (0.0, 0.005, 0.01, 0.02, 0.05):
    run(f"round-2 shape, agreement rate {agree_rate}", [259, 4409], [146, 50], [0.75, agree_rate])
for agree_rate in (0.0, 0.005, 0.01, 0.03):
    run(f"round-1 shape, agreement rate {agree_rate}", [328, 5176], [318, 98], [0.786, agree_rate])
# Without a replacement: one stratum per label (pass, fail).
for n in (100, 150):
    for rates in ((0.0, 0.0), (0.005, 0.005), (0.01, 0.01), (0.02, 0.02), (0.01, 0.05), (0.05, 0.05)):
        run(f"label strata, n = {n} each, rates {rates}", [47880, 20520], [n, n], rates)
