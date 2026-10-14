"""Chronological Overlay & Velocity Matrix — seed sketch (mother).
Source: archive 'Important 14' (2026-05-30), section 3.

Mechanism: isolate clean trend signals from chaotic noise by cutting
history into fixed time blocks and stacking them vertically.
  - ROC: slice historical path into repeating 180-day intervals,
    overlay them within a single 180-day frame.
  - PITCH VECTOR: squash random 'static' to measure the velocity and
    steepness of the long-term trend line.

Toy: synthetic noisy trend, 5 years of daily points. All numbers measured.
Real market data: [UNMEASURABLE] here — needs an actual price series.
"""
import numpy as np

BLOCK = 180  # days per overlay frame


def synth_series(n_days=5 * 365, seed=7, trend=0.05, noise=2.0, cycles=(90, 365)):
    rng = np.random.default_rng(seed)
    t = np.arange(n_days)
    y = trend * t
    for period, amp in zip(cycles, (3.0, 8.0)):
        y += amp * np.sin(2 * np.pi * t / period)
    y += rng.normal(0, noise, n_days)
    return y


def overlay_blocks(y, block=BLOCK):
    n = (len(y) // block) * block
    return y[:n].reshape(-1, block)


def roc_overlay(blocks):
    """Mean path across stacked blocks + per-day rate of change."""
    mean_path = blocks.mean(axis=0)
    roc = np.diff(mean_path, prepend=mean_path[0])
    return mean_path, roc


def pitch_vector(y, block=BLOCK):
    """Squash static: block means -> linear fit = trend velocity/steepness."""
    blocks = overlay_blocks(y, block)
    means = blocks.mean(axis=1)
    x = np.arange(len(means))
    slope, intercept = np.polyfit(x, means, 1)
    resid = means - (slope * x + intercept)
    return slope, float(np.std(resid)), means


if __name__ == "__main__":
    y = synth_series()
    blocks = overlay_blocks(y)
    mean_path, roc = roc_overlay(blocks)
    slope, resid_sd, means = pitch_vector(y)
    print(f"blocks stacked : {blocks.shape[0]} x {blocks.shape[1]} days")
    print(f"mean ROC/day  : {roc.mean():+.5f}  (trend direction + magnitude)")
    print(f"pitch vector  : slope {slope:+.4f} price-units/block, "
          f"resid sd {resid_sd:.3f}")
    print(f"signal/static : {abs(slope) / max(resid_sd, 1e-9):.2f}")
    # [UNMEASURABLE] real market data — needs an actual price series.
