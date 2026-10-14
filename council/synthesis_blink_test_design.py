"""
Chronological Overlay — Blink's test design (experimental-design seat).
Outward-facing falsification harness for synthesis_five_overlay_verified.py.

Every claim the verified synthesis makes is restated here as a BREAKABLE test:
  - what would break it (the break condition),
  - what gets measured,
  - where execution stops (marked at the exact line, per the operator's bar).

The archive's hypothesis is SPLIT and the harness keeps it split: the trend
instrument is tested for recovery; the rhythm failure is FENCED IN CODE
(T6-T8 prove the blind spot mechanically), not hidden, not softened.

Twin's DIVERGE binds: rhythm magnitudes are policy-mirrored, never findings.
Four's battery binds: the 34% is extreme-value statistics; "rhythm found" is
projection.

A stranger runs `python3 this_file.py` and gets pass/fail plus paper designs.

Marking (inherited from the chain):
  [EXECUTED]      ran here on numpy, numbers reported
  [POLICY]        mirrors chosen parameters, not a finding
  [SYNTH]         synthetic series — manufactured, not grown
  [UNMEASURABLE]  cannot run here; exact line marked, measurement designed on paper
"""
import numpy as np
import math

BLOCK, DAYS, TRUE_SLOPE = 180, 1800, 9.0


def series(seed=0, noise_std=1.0, pulse_amp=0.0, pulse_period=None, slope=TRUE_SLOPE):
    # [SYNTH] Alpha's generator, re-derived (not imported) for independence.
    r = np.random.default_rng(seed)
    t = np.arange(DAYS, dtype=float)
    y = (slope / BLOCK) * t + r.normal(0, noise_std, DAYS)
    if pulse_amp > 0 and pulse_period:
        ph = (t % pulse_period) / pulse_period
        y = y - pulse_amp * np.exp(-((ph * pulse_period) ** 2) / (2 * 3.0 ** 2))
    return y


def stack(s, block=BLOCK):
    n = len(s) // block
    return s[:n * block].reshape(n, block), n


def pitch(s, block=BLOCK):
    # [EXECUTED] Alpha's pitch vector + R2, re-derived.
    st, n = stack(s, block)
    m = st.mean(axis=1)
    x = np.arange(n, dtype=float)
    sl, ic = np.polyfit(x, m, 1)
    pred = sl * x + ic
    r2 = 1 - ((m - pred) ** 2).sum() / ((m - m.mean()) ** 2).sum()
    return sl, r2


def rhythm_detect(s, block=BLOCK, k_sigma=3.0):
    # [EXECUTED] Four's detector (Twin's reimplementation), re-derived.
    st, _ = stack(s, block)
    traj = st.mean(axis=0)
    x = np.arange(len(traj), dtype=float)
    lin = np.polyfit(x, traj, 1)
    detr = traj - (lin[0] * x + lin[1])
    strength = float(np.abs(detr).max() / detr.std())
    return strength > k_sigma, strength


# ---------------------------------------------------------------------------
# T1 — Trend recovery fidelity. [EXECUTED]
# Claim: pitch recovers the true slope (+9.00/block).
# Break: |recovered - true| / true > 5% -> the instrument doesn't recover.
# ---------------------------------------------------------------------------
def t1_fidelity():
    sl, r2 = pitch(series())
    err = abs(sl - TRUE_SLOPE) / TRUE_SLOPE
    return err < 0.05, {"pitch": round(sl, 2), "true": TRUE_SLOPE,
                        "rel_err": round(err, 4), "r2": round(r2, 4)}


# ---------------------------------------------------------------------------
# T2 — Slope-agnosticism (Control's check, re-derived). [EXECUTED]
# Claim: recovery is mechanism, not numerology — exact at 3.0/9.0/25.0.
# Break: any slope missed by >5% -> the mechanism is tuned to the test value.
# ---------------------------------------------------------------------------
def t2_slope_agnostic():
    errs = {}
    for s in (3.0, 9.0, 25.0):
        sl, _ = pitch(series(slope=s))
        errs[s] = abs(sl - s) / s
    ok = all(e < 0.05 for e in errs.values())
    return ok, {"rel_err_by_slope": {k: round(v, 4) for k, v in errs.items()}}


# ---------------------------------------------------------------------------
# T3 — Block-invariance of trend. [EXECUTED]
# Claim (Reversed): pitch/day is block-invariant at 90/180/360.
# Break: block-equiv estimates differ by >5% -> the trend is block-relative.
# ---------------------------------------------------------------------------
def t3_block_invariant():
    ests = {}
    for b in (90, 180, 360):
        sl, _ = pitch(series(), block=b)
        ests[b] = sl / b * 180  # block-equiv units
    spread = (max(ests.values()) - min(ests.values())) / TRUE_SLOPE
    return spread < 0.05, {"block_equiv": {k: round(v, 2) for k, v in ests.items()}}


# ---------------------------------------------------------------------------
# T4 — R2 tripwire. [EXECUTED]
# Claim (Twin): R2 warns BEFORE the pitch estimate goes wrong (graceful degradation).
# Test: sweep noise; find where pitch error first exceeds 20%; assert R2 was
#   already collapsed (<0.5) at the step BEFORE — i.e., the warning precedes
#   the failure, it doesn't coincide with it.
# Break: pitch wrong while R2 still high -> the tripwire doesn't warn.
# ---------------------------------------------------------------------------
def t4_tripwire():
    prev_r2, prev_ns = None, None
    for ns in (1, 10, 30, 60, 100, 200, 400, 800, 1600, 3200):
        sl, r2 = pitch(series(noise_std=float(ns), seed=3))
        err = abs(sl - TRUE_SLOPE) / TRUE_SLOPE
        if err > 0.20:
            warned = (prev_r2 is not None and prev_r2 < 0.5)
            return warned, {"failed_at_ns": ns, "err": round(err, 3),
                            "r2_before_failure": round(prev_r2, 3),
                            "verdict": "R2 warned before collapse" if warned else "R2 did NOT warn"}
        prev_r2, prev_ns = r2, ns
    return False, {"verdict": "pitch never failed in sweep — tripwire untested"}


# ---------------------------------------------------------------------------
# T5 — Regime-shift guard. [EXECUTED]
# Claim (Shuffled): one-breakpoint segmented pitch cures naive blindness;
#   break found at block 5 = true 5.
# Break: found break != 5 -> the cure doesn't work.
# ---------------------------------------------------------------------------
def t5_regime_guard():
    t = np.arange(DAYS, dtype=float)
    y2 = np.where(t < 900, 0.05 * t, 0.05 * 900 - 0.05 * (t - 900))
    y2 = y2 + np.random.default_rng(1).normal(0, 1.0, DAYS)
    st, n = stack(y2)
    m = st.mean(axis=1)

    def seg_sse(b):
        if b < 2 or (n - b) < 2:
            return np.inf
        x1, x2 = np.arange(b, dtype=float), np.arange(b, n, dtype=float)
        s1, i1 = np.polyfit(x1, m[:b], 1)
        s2, i2 = np.polyfit(x2, m[b:], 1)
        return float(((m[:b] - (s1 * x1 + i1)) ** 2).sum()
                      + ((m[b:] - (s2 * x2 + i2)) ** 2).sum())

    best = min(range(1, n - 1), key=seg_sse)
    return best == 5, {"found_break": best, "true_break": 5}


# ---------------------------------------------------------------------------
# T6 — Hallucination battery, H1 (Four). [EXECUTED]
# Claim: 34% false rhythms on pure noise; extreme-value theory predicts ~39%.
# This test FENCES the rhythm failure: it proves the "discoveries" are
#   extreme-value statistics, not rhythm. The rate is MECHANISM-honest;
#   calling it "rhythm found" is PROJECTION.
# Break (inverted — the fence breaks if): false rate ~= 0% -> the rhythm
#   claim would survive. It doesn't. Also break if rate deviates far from
#   theory -> the mechanism isn't what we think.
# ---------------------------------------------------------------------------
def t6_hallucination():
    rng = np.random.default_rng(0)
    false = sum(rhythm_detect(rng.normal(0, 5.0, DAYS))[0] for _ in range(100))
    Phi = 0.5 * (1 + math.erf(3.0 / math.sqrt(2)))
    theory = 1 - (2 * Phi - 1) ** 180
    rate = false / 100
    ok = 0.15 < rate < 0.60 and abs(rate - theory) < 0.25
    return ok, {"false_rhythms": f"{false}/100",
                "extreme_value_theory": round(theory, 2),
                "verdict": "rate is statistics, not rhythm" if ok else "MECHANISM MISMATCH"}


# ---------------------------------------------------------------------------
# T7 — Misattribution (Four H4, Twin projection) — CORRECTED. [EXECUTED]
# CORRECTION TO THE SYNTHESIS RECORD: the verified file's prose says H4
#   "detected@180=False" / "invisible", but its own code prints
#   detected@180=True, strength=3.38. The reimplementation here reproduces
#   the CODE's output (True), not the prose. The honest reading: the detector
#   FIRES on period-100 data — but what fires is the ALIASED SHADOW of the
#   true period, not a discovery of it. The method cannot report period=100.
#   This sharpens (not weakens) the verdict: the failure isn't silence,
#   it's misattribution.
# Test: (a) period-100 pulses AND period-180 pulses both fire at block 180
#   -> the detection event carries ZERO bits about the true period
#   (indistinguishable); (b) 5/6 off-block rhythms misattributed (projection).
# Break: detector distinguishes the true periods -> "cannot discover" breaks.
# ---------------------------------------------------------------------------
def _pulse_series(true_period, seed=5, amp=4.0):
    ta = np.arange(DAYS, dtype=float)
    return ((TRUE_SLOPE / BLOCK) * ta
            - amp * np.exp(-(((ta % true_period)) ** 2) / (2 * 3.0 ** 2))
            + np.random.default_rng(seed).normal(0, 1.0, DAYS))


def t7_misattribution():
    det100, s100 = rhythm_detect(_pulse_series(100))  # block=180
    det180, s180 = rhythm_detect(_pulse_series(180))  # block=180
    # Both fire -> the fire says nothing about which period is true.
    indistinguishable = det100 and det180
    proj = 0
    for p in (45, 90, 100, 135, 270, 360):  # [POLICY] sweep set
        d, _ = rhythm_detect(series(pulse_amp=3.0, pulse_period=p))
        if d and p != 180:
            proj += 1
    ok = indistinguishable and proj >= 4
    return ok, {"period100_fires_at_180": det100,
                "period180_fires_at_180": det180,
                "indistinguishable": indistinguishable,
                "off_block_misattributed": f"{proj}/6",
                "correction": "synthesis prose said False/invisible; code prints True/3.38 — "
                              "misattribution, not silence",
                "verdict": "detection carries zero bits about true period" if ok else "FENCE BROKEN"}


# ---------------------------------------------------------------------------
# T8 — Confirmation, not discovery + sweep-hallucination (the fence, in code).
# [EXECUTED]
# Claim: the detector's output is a function of the QUERIED BLOCK, not the
#   data's rhythm. And: sweeping blocks on pure noise MANUFACTURES "discoveries"
#   (discovery-via-sweep IS H1's hallucination machine).
# Test: (a) sweep 12 blocks on pure noise across 3 seeds; assert the hit RATE
#   is consistent with the extreme-value expectation (~34%/block-trial);
#   (b) per-block detections on period-100 data (informational).
# Break: sweep hit rate ~= 0 -> uncalibrated search would be safe (it isn't).
# ---------------------------------------------------------------------------
def t8_confirmation_only():
    adv = _pulse_series(100)
    per_block = {}
    for b in (90, 180, 360):
        d, s = rhythm_detect(adv, block=b)
        per_block[b] = (d, round(s, 2))
    blocks = [45, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]
    hits, trials = 0, 0
    for seed in (9, 10, 11):
        rng = np.random.default_rng(seed)
        noise = rng.normal(0, 5.0, DAYS)
        for b in blocks:
            hits += int(rhythm_detect(noise, block=b)[0])
            trials += 1
    rate = hits / trials
    ok = 0.10 < rate < 0.60  # consistent with ~34% extreme-value expectation
    return ok, {"detections_by_block_trueP100": per_block,
                "sweep_hits_on_pure_noise": f"{hits}/{trials}={rate:.0%}",
                "verdict": "sweep manufactures discoveries at ~predicted rate" if ok
                           else "sweep rate outside expected band"}


# ---------------------------------------------------------------------------
# T9 — Real-trend trial. [UNMEASURABLE] here — the trend verdict trial.
# Break condition for the trend instrument: does the overlay recover a REAL
# trend from REAL noise?
# Paper design:
#   DATA: real time series with INDEPENDENTLY KNOWN trend (documented
#     structural break, injected known slope into real noise, or consensus
#     benchmark series). The trend must be knowable WITHOUT the overlay —
#     else the trial is circular.
#     [UNMEASURABLE] exact line: no real series here.
#   TEST: run pitch; assert recovered slope within x% of known; assert R2
#     tripwire behavior matches T4 (warns before failure on the real series).
#   FALSIFY: (1) pitch misses the known trend while R2 stays high -> the
#     tripwire doesn't transfer; (2) pitch misses AND R2 warned -> instrument
#     correctly reported unreadability (not a failure of the instrument,
#     a success of the guard); (3) block-equiv estimates diverge across
#     90/180/360 on real data -> T3's invariance was synthetic luck.
#   Twin's DIVERGE binds: no T1–T8 magnitude predicts real-data performance.
# ---------------------------------------------------------------------------
def t9_real_trend_paper():
    return {"status": "[UNMEASURABLE]",
            "design": "real series, independently-known trend; pitch recovery "
                      "within x%; R2-tripwire transfer check; block-equiv "
                      "divergence check; falsify on missed-trend-with-high-R2."}


# ---------------------------------------------------------------------------
# T10 — Rhythm discovery: the impossibility fence. [UNMEASURABLE] + conceptual.
# Question: can ANY fixed-block method discover rhythm, or only confirm it?
# The fence (argued, not executed — it is a design constraint):
#   A fixed block b queries period b (and harmonics). Discovery requires
#   searching periods — a different instrument (periodogram/Lomb-Scargle),
#   which needs its OWN calibration (T8 shows uncalibrated search
#   manufactures findings at the extreme-value rate).
#   Therefore: the overlay can never graduate from confirmation to discovery
#   by parameter tuning. It is confirmation COMPLETE — the blind spot is
#   structural, not a bug to fix.
# Paper design for the positive claim (some OTHER instrument discovers):
#   real series with independently-known rhythmic component; periodogram with
#   calibrated false-alarm control; pre-registered period; falsify on
#   misattribution or hallucination at the calibrated rate.
# [UNMEASURABLE] exact lines: no real rhythmic series; no calibrated
#   discovery instrument in this project.
# ---------------------------------------------------------------------------
def t10_discovery_fence_paper():
    return {"status": "[UNMEASURABLE] + structural",
            "design": "fixed-block = confirmation by construction; discovery "
                      "needs a different, calibrated instrument; the overlay's "
                      "blind spot is structural, not fixable by tuning."}


def main():
    print("=== CHRONOLOGICAL OVERLAY — TEST DESIGN (Blink, experimental-design seat) ===")
    print("Target: synthesis_five_overlay_verified.py. numpy only.")
    print("The hypothesis stays split: trend tested, rhythm fenced.\n")
    results = {}
    for name, fn in [("T1_fidelity", t1_fidelity),
                     ("T2_slope_agnostic", t2_slope_agnostic),
                     ("T3_block_invariant", t3_block_invariant),
                     ("T4_tripwire", t4_tripwire),
                     ("T5_regime_guard", t5_regime_guard),
                     ("T6_hallucination", t6_hallucination),
                     ("T7_misattribution", t7_misattribution),
                     ("T8_confirmation_only", t8_confirmation_only)]:
        ok, res = fn()
        results[name] = ok
        print(f"{name} [EXECUTED]: {'PASS' if ok else 'FAIL'} {res}")
    print(f"T9_real_trend: {t9_real_trend_paper()['status']}")
    print(f"   {t9_real_trend_paper()['design']}")
    print(f"T10_discovery_fence: {t10_discovery_fence_paper()['status']}")
    print(f"   {t10_discovery_fence_paper()['design']}")
    print()
    allok = all(results.values())
    print("OVERALL:", "PASS — trend instrument verified; rhythm failure fenced in code; "
          "verdict trials (T9/T10) designed on paper, unfunded." if allok
          else "FAIL — see above.")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
