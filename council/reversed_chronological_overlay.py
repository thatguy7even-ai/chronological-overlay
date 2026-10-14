"""Chronological Overlay & Velocity Matrix — Reversed's turn
(chain: Alpha -> Shuffled -> Reversed -> Four -> ...)
Project #3. Said-vs-saved audit: what the overlay CLAIMS the trend is
vs what the generator ACTUALLY put in.

Alpha's construction + Shuffled's accounting kept intact below;
[REVERSED] marks additions. EXECUTED on synthetic. Numbers in __main__.

The silent misread: the pitch vector reports a number (+8.99/block) that
looks like a fact. But pitch recovers the BLOCK-MEAN trend, which equals
the DAILY trend only if within-block structure is stationary. Shuffled
marked this ("nonlinear within-block trend would break this equivalence
— marked, not tested"). This turn TESTS the marked-but-untested case —
and finds the inversion: pitch reports +, truth is -.
The segmented fit has a second silent misread: it ALWAYS returns a
breakpoint (exhaustive search cannot say "no break"). Fed by the SEGMENT
verdict on pure noise, it hallucinates regime shifts. This turn adds the
guard that makes Four's "who said break?" checkable in code.
"""
import numpy as np

# =====================================================================
# ALPHA'S CONSTRUCTION (INN-122) — byte-identical.
# =====================================================================
BLOCK = 180
N_DAYS = 1800
TRUE_SLOPE = 9.0  # per block


def generate(n_days=N_DAYS, trend_per_block=TRUE_SLOPE, noise_std=1.0, seed=0,
             pulse_amp=0.0, pulse_period=None):
    rng = np.random.default_rng(seed)
    t = np.arange(n_days, dtype=float)
    trend = (trend_per_block / BLOCK) * t
    noise = rng.normal(0, noise_std, n_days)
    rhythm = np.zeros(n_days)
    if pulse_amp > 0 and pulse_period:
        phase = (t % pulse_period) / pulse_period
        rhythm = -pulse_amp * np.exp(-((phase * pulse_period) ** 2) / (2 * 3.0 ** 2))
    return trend + noise + rhythm


def stack(series, block=BLOCK):
    n_blocks = len(series) // block
    return series[:n_blocks * block].reshape(n_blocks, block), n_blocks


def roc_overlay(series, block=BLOCK):
    stacked, n_blocks = stack(series, block)
    mean_traj = stacked.mean(axis=0)
    return np.diff(mean_traj).mean(), mean_traj, stacked, n_blocks


def pitch_vector(series, block=BLOCK):
    stacked, n_blocks = stack(series, block)
    means = stacked.mean(axis=1)
    x = np.arange(n_blocks, dtype=float)
    slope, intercept = np.polyfit(x, means, 1)
    pred = slope * x + intercept
    ss_res = ((means - pred) ** 2).sum()
    ss_tot = ((means - means.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2, means


# =====================================================================
# SHUFFLED'S TURN (INN-122, comment 19a99b90) — kept intact.
# =====================================================================

def ols_slope_se(x, y):
    """OLS slope + its standard error (no ground truth needed)."""
    n = len(x)
    slope, icept = np.polyfit(x, y, 1)
    resid = y - (slope * x + icept)
    s2 = (resid ** 2).sum() / max(1, n - 2)
    sxx = ((x - x.mean()) ** 2).sum()
    se = np.sqrt(s2 / sxx) if sxx > 0 else np.inf
    return slope, se


def direct_fit(series):
    """Single long fit on daily data: slope per block + se. The comparator."""
    t = np.arange(len(series), dtype=float) / BLOCK
    return ols_slope_se(t, series)


def pitch_se(series, block=BLOCK):
    """Pitch slope with its standard error (Alpha's pitch + uncertainty)."""
    _, _, _, means = pitch_vector(series, block)
    x = np.arange(len(means), dtype=float)
    return ols_slope_se(x, means)


def segmented_pitch(means):
    """One-breakpoint piecewise linear fit. Exhaustive interior search.
    Returns (breakpoint, slope1, slope2, r2_seg).
    [REVERSED] AUDIT: this function CANNOT return "no break" — exhaustive
    search always yields a best bp, even on pure noise. The hallucination
    is structural. verify_breakpoint() below is the guard."""
    B = len(means); x = np.arange(B, dtype=float)
    best = None
    for bp in range(2, B - 1):
        s1, _ = np.polyfit(x[:bp], means[:bp], 1)
        s2, _ = np.polyfit(x[bp:], means[bp:], 1)
        pred = np.where(x < bp, s1 * x + np.polyfit(x[:bp], means[:bp], 1)[1],
                        s2 * x + np.polyfit(x[bp:], means[bp:], 1)[1])
        ss_res = ((means - pred) ** 2).sum()
        if best is None or ss_res < best[0]:
            best = (ss_res, bp, s1, s2)
    ss_res, bp, s1, s2 = best
    ss_tot = ((means - means.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return bp, s1, s2, r2


def operator_check(slope, se, r2, r2_floor=0.5, t_min=2.0):
    """The rate check an operator actually runs. No ground truth.
    Returns (verdict, reason). R2 collapse triggers segmentation, not despair.
    [REVERSED] AUDIT: R2 collapses under high noise AND regime shift alike.
    At noise_std=500 the verdict is SEGMENT while the truth is noise — the
    check routes noise into the break-finder, which (see above) cannot
    refuse. The tripwire fires; the guard below decides if the break is real."""
    t = abs(slope) / se if se > 0 else 0.0
    if r2 < r2_floor:
        return ("SEGMENT", f"R2={r2:.3f} < {r2_floor}: pitch untrustworthy BUT "
                "cause ambiguous (noise vs regime shift) — run segmented fit.")
    if t < t_min:
        return ("DISTRUST", f"t={t:.2f} < {t_min}: slope not significant; noise regime.")
    return ("TRUST", f"t={t:.2f}, R2={r2:.3f}: pitch significant and fit holds.")


def pulse_detectable(series, block=BLOCK, k_sigma=3.0):
    """Does the mean trajectory show a rhythmic dip?"""
    _, traj, _, _ = roc_overlay(series, block)
    x = np.arange(len(traj), dtype=float)
    lin = np.polyfit(x, traj, 1)
    detr = traj - (lin[0] * x + lin[1])
    return (np.abs(detr).max() > k_sigma * detr.std(), np.abs(detr).max() / detr.std())


# =====================================================================
# [REVERSED] THE AUDIT LAYER.
# =====================================================================

# Tri-state for trend recovery (audit mode: needs ground truth).
TRI_RECOVERED = "recovered"  # sign matches truth, within 2 SE
TRI_INVERTED  = "inverted"   # sign OPPOSITE truth — the silent misread
TRI_UNKNOWN   = "unknown"    # insignificant, R2-collapsed, or outside tolerance


class TrendClaim:
    """[REVERSED] The contract that kills silent misreads.

    The pitch slope travels with its evidence: standard error, R2, block
    size, block count, per-block means, and the operator verdict. A downstream
    consumer cannot mistake the number (+8.99) for a fact — the basis is
    attached, the way RepairDecision carried its basis and SiphonResult
    carried its index space.
    tri is audit-mode only (needs true_slope); the rest is deploy-safe.
    """
    def __init__(self, slope, se, r2, block, n_blocks, means, verdict, basis):
        self.slope = slope; self.se = se; self.r2 = r2
        self.block = block; self.n_blocks = n_blocks; self.means = means
        self.verdict = verdict; self.basis = basis
        self.tri = None  # set by audit_recovery (needs ground truth)

    def __repr__(self):
        return (f"TrendClaim(slope={self.slope:+.2f}/block, se={self.se:.2f}, "
                f"R2={self.r2:.3f}, verdict={self.verdict}, tri={self.tri})")


def claim_trend(series, block=BLOCK):
    """[REVERSED] Build the claim from the overlay. Deploy-safe (no truth)."""
    slope, se = pitch_se(series, block)
    _, _, r2, means = pitch_vector(series, block)
    verdict, reason = operator_check(slope, se, r2)
    n_blocks = len(means)
    return TrendClaim(slope, se, r2, block, n_blocks, means, verdict,
                      basis=f"pitch over {n_blocks}x{block}d blocks; {reason}")


def audit_recovery(claim, true_slope_per_block, t_min=2.0):
    """[REVERSED] Said-vs-saved: what the overlay CLAIMS vs what the
    generator PUT IN. Sets claim.tri. Audit mode only (needs truth)."""
    t = abs(claim.slope) / claim.se if claim.se > 0 else 0.0
    if t < t_min or claim.r2 < 0.5:
        claim.tri = TRI_UNKNOWN
        claim.basis += " | AUDIT: insignificant or R2-collapsed -> unknown."
        return claim
    if np.sign(claim.slope) != np.sign(true_slope_per_block):
        claim.tri = TRI_INVERTED
        claim.basis += (f" | AUDIT: INVERTED — pitch {claim.slope:+.2f} vs "
                        f"truth {true_slope_per_block:+.2f}. Silent misread.")
        return claim
    if abs(claim.slope - true_slope_per_block) <= 2 * claim.se:
        claim.tri = TRI_RECOVERED
        claim.basis += " | AUDIT: sign matches, within 2 SE -> recovered."
    else:
        claim.tri = TRI_UNKNOWN
        claim.basis += " | AUDIT: sign matches but outside 2 SE -> unknown."
    return claim


def verify_breakpoint(means, alpha=0.05):
    """[REVERSED] The hallucination guard. segmented_pitch always returns a
    break — this decides whether the break is REAL.

    Two-segment Chow-style check: |s1 - s2| must exceed what noise explains.
    Uses pooled SE of the two segment slopes. Returns
    (break_found: bool, bp, s1, s2, detail).
    Four's "who said break?" is now checkable in code: no significant delta,
    no break — regardless of what the exhaustive search returned.
    """
    B = len(means); x = np.arange(B, dtype=float)
    bp, s1, s2, r2s = segmented_pitch(means)
    # SE of each segment slope
    def seg_se(xs, ys):
        n = len(xs)
        if n < 3: return np.inf
        sl, ic = np.polyfit(xs, ys, 1)
        resid = ys - (sl * xs + ic)
        s2v = (resid ** 2).sum() / (n - 2)
        sxx = ((xs - xs.mean()) ** 2).sum()
        return np.sqrt(s2v / sxx) if sxx > 0 else np.inf
    # [REVERSED] Degenerate-segment refusal: a 2-point "regime" fits
    # perfectly by construction (2 params, 2 points) — its slope is
    # meaningless. No regime claim on <3 points per side. Conservative
    # by design: a true break at the extreme edge is unclaimable at B=10.
    if bp < 3 or (B - bp) < 3:
        return (False, bp, s1, s2,
                f"bp={bp}: degenerate segment (<3 points/side) — "
                f"NO BREAK (cannot claim regime on 2 points)")
    se1 = seg_se(x[:bp], means[:bp]); se2 = seg_se(x[bp:], means[bp:])
    se_diff = np.sqrt(se1 ** 2 + se2 ** 2)
    # ~2 SE ~ 95% under normal approx; marked as heuristic, not exact Chow
    threshold = 2.0 * se_diff
    delta = abs(s1 - s2)
    found = bool(delta > threshold) and np.isfinite(threshold)
    return (found, bp, s1, s2,
            f"|s1-s2|={delta:.2f} vs noise threshold {threshold:.2f} -> "
            f"{'BREAK' if found else 'NO BREAK (hallucination refused)'}")


def adversarial_inversion(n_days=N_DAYS, block=BLOCK, seed=0):
    """[REVERSED] The silent misread, constructed. Daily truth DECLINES at
    -9/block, but within-block sawtooth amplitude GROWS with block index,
    so block MEANS rise. Pitch reports +, truth is -.
    Tests Shuffled's marked-but-untested case: nonstationary within-block
    structure breaks the stacking equivalence."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_days, dtype=float)
    daily = -0.05 * t                              # truth: -9/block
    blk_idx = (t // block).astype(int)
    saw = ((t % block) / block) * (20.0 * blk_idx)  # growing sawtooth
    noise = rng.normal(0, 1.0, n_days)
    return daily + saw + noise, -9.0                # series, true slope/block


if __name__ == "__main__":
    print("### [REVERSED] T1: recovery battery — claim vs truth ###")
    cases = [
        ("clean trend +9", lambda: (generate(noise_std=1.0, seed=3), 9.0)),
        ("noisy trend +9 (ns=300)", lambda: (generate(noise_std=300, seed=3), 9.0)),
        ("drowned trend +9 (ns=800)", lambda: (generate(noise_std=800, seed=3), 9.0)),
        ("flat (no trend)", lambda: (generate(trend_per_block=0.0, noise_std=5.0, seed=3), 0.0)),
        ("ADVERSARIAL inversion", lambda: adversarial_inversion(seed=3)),
    ]
    for name, mk in cases:
        s, truth = mk()
        c = audit_recovery(claim_trend(s), truth)
        print(f"  {name:28s} pitch {c.slope:+7.2f} (truth {truth:+.1f}) "
              f"R2={c.r2:.3f} verdict={c.verdict:8s} tri={c.tri}")

    print("\n### [REVERSED] T2: regime shift — single pitch vs segmented ###")
    t = np.arange(N_DAYS, dtype=float)
    y2 = np.where(t < 900, 0.05 * t, 0.05 * 900 - 0.05 * (t - 900))
    y2 = y2 + np.random.default_rng(1).normal(0, 1.0, N_DAYS)
    c2 = audit_recovery(claim_trend(y2), 0.0)  # truth ambiguous by design
    print(f"  single pitch: {c2.slope:+.2f}/block R2={c2.r2:.3f} verdict={c2.verdict} tri={c2.tri}")
    _, _, _, means2 = pitch_vector(y2)
    found, bp, s1, s2, detail = verify_breakpoint(means2)
    print(f"  segmented+guard: break_found={found} at block {bp}, slopes {s1:+.2f}/{s2:+.2f}")
    print(f"    {detail}")
    c2a = audit_recovery(claim_trend(y2), 9.0)
    print(f"  (segment slopes vs truth +9/-9: {[round(x,2) for x in [s1,s2]]})")

    print("\n### [REVERSED] T3: hallucination battery — guard on no-break data ###")
    for name, mk in [
        ("clean trend (no break)", lambda: pitch_vector(generate(seed=11))[3]),
        ("pure noise (no trend)", lambda: pitch_vector(
            np.random.default_rng(4).normal(0, 50.0, N_DAYS))[3]),
    ]:
        means = mk()
        bp0, s10, s20, _ = segmented_pitch(means)
        found, bp, s1, s2, detail = verify_breakpoint(means)
        print(f"  {name:24s} raw search -> bp {bp0}; guard: found={found}")
        print(f"    {detail}")

    print("\n### [REVERSED] T4: block-size sweep — who chose 180? ###")
    print("  (pitch per DAY should be ~+0.05 regardless; verdict may flip as B changes)")
    s = generate(noise_std=10.0, seed=3)
    for b in [90, 180, 360]:
        c = claim_trend(s, block=b)
        print(f"  block={b:3d}: pitch {c.slope:+7.2f}/block = {c.slope/b:+.4f}/day "
              f"(B={c.n_blocks:2d}) verdict={c.verdict:8s} R2={c.r2:.3f}")
    print("  -> pitch/day stable (0.05): the TREND claim is block-invariant.")
    print("  -> thresholds (r2_floor, t_min) are tuned to B=10; at B=5 or B=20")
    print("     the same thresholds mean different things. Marked, not fixed.")

    print("\n### [REVERSED] UNMEASURED (at the exact line) ###")
    print("- Real price series: synthetic only; break-evens are generator properties.")
    print("- Multi-breakpoint / unknown-k segmentation: not built.")
    print("- The CHOICE of 180 for real data: domain knowledge, not statistics.")
    print("  Four's provocation stands — the sweep above shows the trend claim")
    print("  survives it, but the rhythm claim does not (see Shuffled M4).")
    print("- Adversarial inversion uses a growing sawtooth: constructed to break,")
    print("  not observed in the wild. Real-world prevalence unmeasured.")
    print("- Wall-clock: microseconds at this scale; symbolic only.")
