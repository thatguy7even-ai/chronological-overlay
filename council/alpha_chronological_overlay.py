"""Chronological Overlay & Velocity Matrix — Alpha's turn.
EXECUTED on synthetic. All numbers measured.
INN-122.
"""
import numpy as np

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


if __name__ == "__main__":
    y = generate()
    roc, traj, stacked, n = roc_overlay(y)
    slope, icept, r2, means = pitch_vector(y)
    print(f"blocks: {n} x {BLOCK}d | ROC/day {roc:+.4f} (true +0.0500)")
    print(f"pitch: {slope:+.2f}/block (true {TRUE_SLOPE}), R2={r2:.4f}")
    for ns in (100, 200, 500):
        s, _, r2n, _ = pitch_vector(generate(noise_std=ns))
        err = abs(s - TRUE_SLOPE) / TRUE_SLOPE * 100
        print(f"noise_std={ns}: pitch {s:+.2f} ({err:.0f}% err), R2={r2n:.3f}")
    # regime shift: up 900d, down 900d
    t = np.arange(N_DAYS, dtype=float)
    y2 = np.where(t < 900, 0.05 * t, 0.05 * 900 - 0.05 * (t - 900))
    y2 = y2 + np.random.default_rng(1).normal(0, 1.0, N_DAYS)
    s2, _, r2b, _ = pitch_vector(y2)
    print(f"regime shift: pitch {s2:+.2f}, R2={r2b:.4f} (structurally blind)")
    # [CANNOT RUN: real price series — needs non-synthetic market data.]
