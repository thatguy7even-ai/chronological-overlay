"""Chronological Overlay & Velocity Matrix — Four's turn
(chain: Alpha -> Shuffled -> Reversed -> Four -> ...)
Project #3. The ground truth provocation: the hallucination battery.

Reversed answered "who chose 180?" for the TREND (block-invariant, trust at
90/180/360). This turn asks it for the RHYTHM: does the overlay FIND periodic
structure, or PROJECT block-periodic structure onto non-periodic data?

Alpha's construction + Shuffled's accounting + Reversed's audit kept intact;
[FOUR] marks additions. EXECUTED on synthetic. Numbers in __main__.

The provocation: pulse_detectable() tests period == block BY CONSTRUCTION.
It cannot test any other period. If the data's rhythm lives at period 100 and
the blocks stack at 180, the overlay is blind to it — and worse, may hallucinate
a rhythm at 180 that isn't there. The method's period IS the block size.
That is manufacture, not discovery.
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
    # [FOUR] GROUND TRUTH PROVENANCE for rhythm: pulse_amp and pulse_period
    # are MANUFACTURED parameters. On real data there is no pulse_period knob —
    # the overlay must DISCOVER periodicity without knowing it in advance.
    # Every "rhythm detected" below is measured against MANUFACTURED rhythm.
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
    [REVERSED] AUDIT: cannot return "no break" — guard is verify_breakpoint()."""
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
    """The rate check an operator actually runs. No ground truth."""
    t = abs(slope) / se if se > 0 else 0.0
    if r2 < r2_floor:
        return ("SEGMENT", f"R2={r2:.3f} < {r2_floor}: pitch untrustworthy BUT "
                "cause ambiguous (noise vs regime shift) — run segmented fit.")
    if t < t_min:
        return ("DISTRUST", f"t={t:.2f} < {t_min}: slope not significant; noise regime.")
    return ("TRUST", f"t={t:.2f}, R2={r2:.3f}: pitch significant and fit holds.")


def pulse_detectable(series, block=BLOCK, k_sigma=3.0):
    """Does the mean trajectory show a rhythmic dip?
    [FOUR] AUDIT: tests period == block BY CONSTRUCTION. The detrended mean
    trajectory has length `block`; any periodic structure it reveals is at
    period `block` (or its harmonics). A rhythm at any OTHER period is invisible
    here — not tested, not found, not reported. The method's period IS the
    block size. On real data, where the period is unknown, this is a search
    with one fixed query."""
    _, traj, _, _ = roc_overlay(series, block)
    x = np.arange(len(traj), dtype=float)
    lin = np.polyfit(x, traj, 1)
    detr = traj - (lin[0] * x + lin[1])
    return (np.abs(detr).max() > k_sigma * detr.std(), np.abs(detr).max() / detr.std())


# =====================================================================
# [REVERSED] THE AUDIT LAYER — kept intact.
# =====================================================================

TRI_RECOVERED = "recovered"
TRI_INVERTED  = "inverted"
TRI_UNKNOWN   = "unknown"


class TrendClaim:
    """[REVERSED] The contract that kills silent misreads."""
    def __init__(self, slope, se, r2, block, n_blocks, means, verdict, basis):
        self.slope = slope; self.se = se; self.r2 = r2
        self.block = block; self.n_blocks = n_blocks; self.means = means
        self.verdict = verdict; self.basis = basis
        self.tri = None

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
    """[REVERSED] The hallucination guard for breaks."""
    B = len(means); x = np.arange(B, dtype=float)
    bp, s1, s2, r2s = segmented_pitch(means)
    def seg_se(xs, ys):
        n = len(xs)
        if n < 3: return np.inf
        sl, ic = np.polyfit(xs, ys, 1)
        resid = ys - (sl * xs + ic)
        s2v = (resid ** 2).sum() / (n - 2)
        sxx = ((xs - xs.mean()) ** 2).sum()
        return np.sqrt(s2v / sxx) if sxx > 0 else np.inf
    if bp < 3 or (B - bp) < 3:
        return (False, bp, s1, s2,
                f"bp={bp}: degenerate segment (<3 points/side) — "
                f"NO BREAK (cannot claim regime on 2 points)")
    se1 = seg_se(x[:bp], means[:bp]); se2 = seg_se(x[bp:], means[bp:])
    se_diff = np.sqrt(se1 ** 2 + se2 ** 2)
    threshold = 2.0 * se_diff
    delta = abs(s1 - s2)
    found = bool(delta > threshold) and np.isfinite(threshold)
    return (found, bp, s1, s2,
            f"|s1-s2|={delta:.2f} vs noise threshold {threshold:.2f} -> "
            f"{'BREAK' if found else 'NO BREAK (hallucination refused)'}")


def adversarial_inversion(n_days=N_DAYS, block=BLOCK, seed=0):
    """[REVERSED] The silent misread, constructed."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_days, dtype=float)
    daily = -0.05 * t
    blk_idx = (t // block).astype(int)
    saw = ((t % block) / block) * (20.0 * blk_idx)
    noise = rng.normal(0, 1.0, n_days)
    return daily + saw + noise, -9.0


# =====================================================================
# [FOUR] THE HALLUCINATION BATTERY.
# =====================================================================

# [FOUR] RhythmClaim: the rhythm counterpart to TrendClaim.
# The critical field is period_tested — ALWAYS == block. The overlay cannot
# test any other period. A "no rhythm detected" verdict means "no rhythm AT
# PERIOD == BLOCK detected," not "no rhythm." The claim's scope is the method's
# blind spot, marked here so downstream does not over-read it.
class RhythmClaim:
    def __init__(self, detected, strength, block, k_sigma, basis):
        self.detected = detected
        self.strength = strength      # max|detr| / std, in sigma units
        self.block = block
        self.period_tested = block    # [FOUR] ALWAYS == block. The blind spot.
        self.k_sigma = k_sigma
        self.basis = basis

    def __repr__(self):
        return (f"RhythmClaim(detected={self.detected}, strength={self.strength:.2f}σ, "
                f"period_tested={self.period_tested} (=block; other periods untested))")


def claim_rhythm(series, block=BLOCK, k_sigma=3.0):
    """[FOUR] Build the rhythm claim. Deploy-safe (no truth needed)."""
    detected, strength = pulse_detectable(series, block=block, k_sigma=k_sigma)
    return RhythmClaim(
        detected, strength, block, k_sigma,
        basis=(f"detrended mean trajectory over {block}d blocks; "
               f"max|dev|={strength:.2f}σ vs threshold {k_sigma}σ. "
               f"Period tested == block == {block}; all other periods untested."))


def noise_hallucination_rate(n_trials=100, n_days=N_DAYS, block=BLOCK,
                             noise_std=5.0, k_sigma=3.0, seed=0):
    """[FOUR] Feed pure noise. Count false rhythm claims.
    If the detector fires on noise, the 'rhythm' is in the method, not the data.
    EXECUTED."""
    rng = np.random.default_rng(seed)
    false = 0
    for _ in range(n_trials):
        noise = rng.normal(0, noise_std, n_days)
        rc = claim_rhythm(noise, block=block, k_sigma=k_sigma)
        if rc.detected:
            false += 1
    return false, n_trials, false / n_trials


def period_mismatch_test(periods=(90, 180, 270, 360), block=BLOCK,
                         pulse_amp=3.0, noise_std=1.0, seed=0):
    """[FOUR] Rhythm at true period P, overlay stacking at block B.
    If detection only fires when P == B, the blocks are PROJECTING rhythm,
    not DISCOVERING it. A discovery method finds the rhythm wherever it lives.
    EXECUTED."""
    results = []
    for p in periods:
        s = generate(pulse_amp=pulse_amp, pulse_period=p,
                     noise_std=noise_std, seed=seed)
        rc = claim_rhythm(s, block=block)
        results.append((p, rc.detected, rc.strength))
    return results


def phase_sensitivity_test(n_phases=8, pulse_period=180, block=BLOCK,
                           pulse_amp=3.0, noise_std=1.0, seed=0):
    """[FOUR] Same rhythm, different alignment to block boundaries.
    Slices a long series at offsets (simulates phase shift of rhythm vs blocks).
    If detection varies with phase, the BLOCK ALIGNMENT is doing the work —
    the rhythm is not robustly present, it is alignment-dependent.
    Manufactured alignment, not grown rhythm. EXECUTED."""
    full = generate(n_days=N_DAYS + pulse_period, pulse_amp=pulse_amp,
                    pulse_period=pulse_period, noise_std=noise_std, seed=seed)
    results = []
    for i in range(n_phases):
        offset = i * (pulse_period // n_phases)
        s = full[offset:offset + N_DAYS]
        rc = claim_rhythm(s, block=block)
        results.append((offset, rc.detected, rc.strength))
    return results


def adversarial_rhythm(n_days=N_DAYS, block=BLOCK, seed=0):
    """[FOUR] The rhythm inversion, constructed (parallel to Reversed's trend
    inversion). A rhythm whose period is NOT the block size, plus noise shaped
    to create a spurious block-periodic dip. Tests whether the overlay claims
    a rhythm at period==block when the TRUE rhythm lives elsewhere.
    Returns (series, true_period). EXECUTED."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_days, dtype=float)
    # TRUE rhythm: period 100, moderate amplitude — the grown structure.
    true_period = 100
    phase = (t % true_period) / true_period
    true_rhythm = -4.0 * np.exp(-((phase * true_period) ** 2) / (2 * 3.0 ** 2))
    # SPURIOUS block-periodic artifact: tiny dip aligned to block boundaries.
    # Simulates e.g. a data-processing artifact (batch effects, calendar effects).
    # MANUFACTURED: this is what the overlay might mistake for rhythm.
    blk_phase = (t % block) / block
    spurious = -1.5 * np.exp(-((blk_phase * block) ** 2) / (2 * 5.0 ** 2))
    noise = rng.normal(0, 1.0, n_days)
    trend = (TRUE_SLOPE / BLOCK) * t
    return trend + true_rhythm + spurious + noise, true_period


if __name__ == "__main__":
    # --- Reversed's battery, reproduced (verify intact) ---
    print("### [REVERSED] T4 reproduced: block-size sweep (trend) ###")
    s = generate(noise_std=10.0, seed=3)
    for b in [90, 180, 360]:
        c = claim_trend(s, block=b)
        print(f"  block={b:3d}: pitch {c.slope:+7.2f}/block = {c.slope/b:+.4f}/day "
              f"(B={c.n_blocks:2d}) verdict={c.verdict:8s} R2={c.r2:.3f}")

    print("\n### [FOUR] H1: noise hallucination rate (pure noise, 100 trials) ###")
    false, total, rate = noise_hallucination_rate()
    print(f"  false rhythm claims: {false}/{total} = {rate:.1%}")
    print(f"  [FOUR] On pure noise, the detector fires {rate:.0%} of the time.")
    print(f"  Every firing is a hallucinated rhythm — the method projecting")
    print(f"  periodicity onto non-periodic data. k_sigma=3.0 is not conservative")
    print(f"  enough for a {BLOCK}-point trajectory (expected max|N(0,1)| ~ 3σ).")

    print("\n### [FOUR] H2: period mismatch (true period P vs block B=180) ###")
    for p, detected, strength in period_mismatch_test():
        mark = " <-- P==B" if p == BLOCK else ""
        print(f"  true period {p:3d}: detected={str(detected):5s} strength={strength:.2f}σ{mark}")
    print("  [FOUR] If detection fires at P==B but misses P=90/270/360, the overlay")
    print("  does not discover rhythm — it confirms rhythm at its own block size.")

    print("\n### [FOUR] H3: phase sensitivity (same rhythm, 8 alignments) ###")
    detects = 0
    for offset, detected, strength in phase_sensitivity_test():
        print(f"  offset {offset:3d}: detected={str(detected):5s} strength={strength:.2f}σ")
        detects += detected
    print(f"  [FOUR] Detected at {detects}/8 phases. If <8/8, the rhythm claim is")
    print(f"  alignment-dependent — the BLOCKS are doing the finding, not the data.")

    print("\n### [FOUR] H4: adversarial rhythm (true period 100, spurious at 180) ###")
    s_adv, true_p = adversarial_rhythm(seed=5)
    rc_adv = claim_rhythm(s_adv, block=BLOCK)
    print(f"  true rhythm period: {true_p} (grown in the data)")
    print(f"  overlay tests period: {rc_adv.period_tested} (manufactured by blocks)")
    print(f"  detected={rc_adv.detected}, strength={rc_adv.strength:.2f}σ")
    print(f"  [FOUR] The overlay cannot see period {true_p} — it only queries {BLOCK}.")
    print(f"  A 'rhythm detected' here would be the SPURIOUS block artifact,")
    print(f"  not the true rhythm. The method finds what it looks for.")

    print("\n### [FOUR] LOAD-BEARING ASSUMPTION (rhythm) ###")
    print("  Stacking at block B and detrending reveals periodic structure INHERENT")
    print("  in the data, rather than imposing block-periodic structure ON the data.")
    print("  H1-H4 test this. If H1 fires often, H2 misses off-block periods, or H3")
    print("  varies with phase: the assumption FAILS — the rhythm is projected,")
    print("  not discovered. Reversed's trend claim survives 'who chose 180';")
    print("  the rhythm claim does not. Choice of block for RHYTHM on real data")
    print("  is domain knowledge (or guesswork), not statistics.")

    print("\n### [FOUR] UNMEASURED (at the exact line) ###")
    print("- Real price series rhythm: synthetic only; H1-H4 are generator properties.")
    print("- Multi-period search (spectral/periodogram): not built — the overlay")
    print("  as constructed cannot do it. A real rhythm-finder would need one.")
    print("- The CHOICE of block for rhythm on real data: domain knowledge.")
    print("  Reversed's line, confirmed and extended: statistics cannot choose it.")
    print("- Wall-clock: microseconds at this scale; symbolic only.")
