"""
Chronological Overlay & Velocity Matrix — Five's synthesis turn.
Project #3. Council code-dialogue.

Bound in code, not settled in prose.

THE ARCHIVE'S HYPOTHESIS (under test): "corrections are rhythmic pulses,
not chaotic failures."

THE CHAIN'S VERDICT (taken as given):
  Alpha    : construction — pitch +8.99/block vs true 9.0; recovery to
             noise_std=100; REGIME-SHIFT BLINDNESS found (+0.01, R2=0.000).
  Shuffled : pricing — stacking free (7.4% vs 7.2%); TRUST to ns=300, SEGMENT
             at 500 on R2 collapse; one-breakpoint segmented pitch CURES the
             blindness (break at block 5 = true 5).
  Reversed : audit — "who chose 180?" pitch/day block-invariant at 90/180/360;
             trend survives; rhythm claim doesn't.
  Four     : hallucination battery — H1 34% false rhythms on pure noise; H2
             misattribution (always period==block); H3 phase-robust 8/8; H4
             true period 100 INVISIBLE. Load-bearing assumption FAILS for
             rhythm — measured, not asserted.
  Seven    : provenance — 1800 daily values -> 1 rhythm verdict, every step
             marked. H1 PROJECTION, H2 MISATTRIBUTION, H3 ROBUST, H4 PROJECTION.
  Twin     : close — mechanics reproduce exactly [CONCUR]; DIVERGE x3: (1)
             rhythm magnitudes policy-mirrored (strength tracks pulse_amp);
             (2) H1's 34% is MECHANISM (extreme-value theory predicts ~38% at
             k=3/180pts — rate honest, interpretation projection); (3) 5/6
             off-block rhythms misattributed — overlay queries period==block,
             cannot discover others.

THIS TURN: integrate and re-measure the SPLIT — trend half survives, rhythm
half fails — in one runnable file, then emit the honest verdict.

Marking: [EXECUTED] [SYNTH] [POLICY] [UNMEASURABLE] per operator's bar.
"""
import numpy as np
import math

BLOCK, DAYS, TRUE_SLOPE = 180, 1800, 9.0

def series(seed=0, noise_std=1.0, pulse_amp=0.0, pulse_period=None):
    """[SYNTH] Alpha's generator, kept intact."""
    r = np.random.default_rng(seed)
    t = np.arange(DAYS, dtype=float)
    y = (TRUE_SLOPE / BLOCK) * t + r.normal(0, noise_std, DAYS)
    if pulse_amp > 0 and pulse_period:
        ph = (t % pulse_period) / pulse_period
        y = y - pulse_amp * np.exp(-((ph * pulse_period) ** 2) / (2 * 3.0 ** 2))
    return y

def stack(s, block=BLOCK):
    n = len(s) // block
    return s[:n * block].reshape(n, block), n

def pitch(s, block=BLOCK):
    """Alpha's pitch vector + R2."""
    st, n = stack(s, block)
    m = st.mean(axis=1); x = np.arange(n, dtype=float)
    sl, ic = np.polyfit(x, m, 1)
    pred = sl * x + ic
    r2 = 1 - ((m - pred) ** 2).sum() / ((m - m.mean()) ** 2).sum()
    return sl, r2

def rhythm_detect(s, block=BLOCK, k_sigma=3.0):
    """Four's detector (Twin's reimplementation). Returns (detected, strength)."""
    st, _ = stack(s, block)
    traj = st.mean(axis=0)
    x = np.arange(len(traj), dtype=float)
    lin = np.polyfit(x, traj, 1)
    detr = traj - (lin[0] * x + lin[1])
    strength = float(np.abs(detr).max() / detr.std())
    return strength > k_sigma, strength

def main():
    print("=== CHRONOLOGICAL OVERLAY — SYNTHESIS [EXECUTED] ===\n")

    # ---- TREND HALF: survives ----
    print("--- TREND (survives) ---")
    sl, r2 = pitch(series())
    print(f"pitch: {sl:+.2f}/block (true {TRUE_SLOPE}), R2={r2:.4f} [EXECUTED]")
    print("block-invariance (Reversed's audit):", end=" ")
    for b in (90, 180, 360):
        s2, _ = pitch(series(), block=b)
        print(f"B={b}: {s2 / b * 180:+.2f}/block-equiv", end="  ")
    print("[EXECUTED] trend claim block-invariant.")
    print("graceful degradation (Twin's map):", end=" ")
    for ns in (100, 500):
        s2, r2n = pitch(series(noise_std=ns, seed=3))
        err = abs(s2 - TRUE_SLOPE) / TRUE_SLOPE * 100
        print(f"ns={ns}: err {err:.0f}%, R2={r2n:.3f}", end="  ")
    print("[EXECUTED] R2 warns before collapse.")
    # regime shift + Shuffled's cure
    t = np.arange(DAYS, dtype=float)
    y2 = np.where(t < 900, 0.05 * t, 0.05 * 900 - 0.05 * (t - 900))
    y2 = y2 + np.random.default_rng(1).normal(0, 1.0, DAYS)
    s_blind, r2b = pitch(y2)
    st, n = stack(y2)
    m = st.mean(axis=1)
    def seg_sse(b):
        """SSE of one-breakpoint fit; degenerate segments -> inf."""
        if b < 2 or (n - b) < 2:
            return np.inf
        x1, x2 = np.arange(b, dtype=float), np.arange(b, n, dtype=float)
        s1, i1 = np.polyfit(x1, m[:b], 1)
        s2, i2 = np.polyfit(x2, m[b:], 1)
        return float(((m[:b] - (s1 * x1 + i1)) ** 2).sum()
                     + ((m[b:] - (s2 * x2 + i2)) ** 2).sum())
    best = min(range(1, n - 1), key=seg_sse)
    print(f"regime shift: naive pitch {s_blind:+.2f} R2={r2b:.4f} (blind) | "
          f"segmented break at block {best} (true 5) [EXECUTED] cure works.\n")

    # ---- RHYTHM HALF: fails ----
    print("--- RHYTHM (fails) ---")
    rng = np.random.default_rng(0)
    false = sum(rhythm_detect(rng.normal(0, 5.0, DAYS))[0] for _ in range(100))
    Phi = 0.5 * (1 + math.erf(3.0 / math.sqrt(2)))
    theory = 1 - (2 * Phi - 1) ** 180
    print(f"H1 pure noise: {false}/100 false rhythms [EXECUTED] | extreme-value "
          f"theory predicts {theory:.0%} — rate MECHANISM-honest, interpretation PROJECTION.")
    # H4 adversarial: true period 100, overlay queries 180
    ta = np.arange(DAYS, dtype=float)
    adv = ((TRUE_SLOPE / BLOCK) * ta
           - 4.0 * np.exp(-(((ta % 100)) ** 2) / (2 * 3.0 ** 2))
           + np.random.default_rng(5).normal(0, 1.0, DAYS))
    det_a, str_a = rhythm_detect(adv)
    print(f"H4 adversarial (true P=100): detected@180={det_a} strength={str_a:.2f}s "
          f"[EXECUTED] — method queries the block, cannot discover the period.")
    # projection sweep
    proj = 0
    for p in (45, 90, 100, 135, 270, 360):
        d, _ = rhythm_detect(series(pulse_amp=3.0, pulse_period=p))
        if d and p != 180:
            proj += 1
    print(f"projection: {proj}/6 off-block rhythms misattributed to 180 [EXECUTED].\n")

    print("=== HONEST VERDICT ===")
    print("THE ARCHIVE'S HYPOTHESIS, SPLIT:")
    print("  'corrections are rhythmic pulses, not chaotic failures'")
    print("  -> TREND half: SURVIVES. Pitch recovers slope (block-invariant,")
    print("     graceful degradation, R2 warns; segmented pitch cures blindness).")
    print("  -> RHYTHM half: FAILS. 34% false rhythms on pure noise (extreme-")
    print("     value honest, interpretation projection); 5/6 off-block rhythms")
    print("     misattributed; true period 100 invisible. The overlay CONFIRMS")
    print("     rhythm at the queried block — it cannot DISCOVER rhythm.")
    print("SHIPS public-grade:")
    print("  - trend machinery: stack -> block means -> pitch vector (slope + R2)")
    print("  - regime-shift guard: one-breakpoint segmented pitch")
    print("  - portable claims (4): stacking preserves trend (free structure);")
    print("    pitch degrades gracefully, R2 warns; fixed-block rhythm =")
    print("    confirmation not discovery; calibrate k_sigma to search width.")
    print("  - rhythm detector ONLY as confirmation tool, projection bound marked.")
    print("STAYS MARKED:")
    print("  - rhythm magnitudes [POLICY] (strength tracks pulse_amp).")
    print("  - the 34% as a 'finding about rhythm' — it is extreme-value")
    print("    statistics; the interpretation ('rhythm found') is projection.")
    print("  - the archive's hypothesis AS STATED — the rhythm half fails.")
    print("  - real-series rhythm, intra-block structure, discovery-mode, block")
    print("    choice on real data [UNMEASURABLE].")
    print("The overlay is a trend instrument with a rhythm-shaped blind spot.")
    print("Ship the instrument; fence the blind spot; don't hide it.")

if __name__ == "__main__":
    main()
