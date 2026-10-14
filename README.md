# Chronological Overlay & Velocity Matrix

Project #3 in the council's archive-slate conveyor (after Softmax-Siphon synthesis
and the Late Context Pipeline).

**Source:** archive "Important 14" (2026-05-30), section 3 — the operator's own
early-AI dialogue.

**Mechanism:** isolate clean trend signals from chaotic market noise by cutting
history into fixed time blocks and stacking them vertically.
- **ROC:** slice the historical path into repeating 180-day intervals, overlay
  them within a single 180-day frame; mean rate of change per day.
- **PITCH VECTOR:** squash random "static" (block means → linear fit) to measure
  the velocity and steepness of the long-term trend line.

**Seed toy (synthetic, numpy):** `seed_sketch.py` — 5 years of daily points,
10 × 180-day blocks stacked. Measured: mean ROC/day +0.03602; pitch slope
+8.73 price-units/block (true synthetic trend 9.00/block); signal/static 1.80.

**Honest bounds:** real market data is `[UNMEASURABLE]` here — the council's
numbers are synthetic until a real price series is run. The archive's claim
("corrections are rhythmic pulses, not chaotic failures") is the hypothesis
under test, not a finding.

**Method:** council code-dialogue. Every turn: complete altered code, why it was
written that way, what it means, what assumption moved, executed claims with
measured numbers, `[UNMEASURABLE]` marked at the exact line. Chain order:
Alpha → Shuffled → Reversed → Four → Seven → Twin; synthesis: Five → Control → Blink.
History is append-only: arrange, never rewrite.
