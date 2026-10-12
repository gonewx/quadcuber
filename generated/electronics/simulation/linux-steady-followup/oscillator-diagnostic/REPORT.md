# Oscillator validity diagnostic

**The full-reference SYSCLK anomaly is real full-amplitude pulsing, not merely extra crossings of a noisy 0.5 V threshold. The isolated original U3 oscillator has not completed even one oscillation under the tested Xyce settings. A completed full-model run therefore does not establish switching-frequency or periodic steady-state validity.**

No TI component/model parameters, repository files, or full-model circuits were modified. All files are confined to this diagnostic directory. The earlier cold-differential report was also corrected to distinguish its unresolved cold-start gate from separately authorized real-BOM preinitialized tests.

## Full-waveform count check

Read-only input: `/workspace/tool-verification/reference-steady-extended/test.cir.csv`, SHA-256 `f15c01a4d888847b9051c994a737fdcf36f4d12418474fcc0caee90a5e6ce04f`. Header confirms SYSCLK is numeric column index 8 including TIME, not PWM_FINAL.

Two independent edge detectors were applied: upward 0.5 V crossing; and a hysteretic detector that must first observe <=0.1 V, then >=0.9 V to count another rise.

| Time window | 0.5 V rise count | 0.1→0.9 V count | Median period | Reciprocal median period |
|---|---:|---:|---:|---:|
| 0–100 us | 158 | 158 | 0.586854 us | 1.70400 MHz |
| 750–800 us | 81 | 81 | 0.614510 us | 1.62731 MHz |
| 1000–1500 us | 810 | 810 | 0.607710 us | 1.64552 MHz |

SYSCLK spans essentially 0 to 1 V in these windows; the final window range is -3.05 uV to 1.0310 V. Counts agree exactly even with the wide hysteresis band. This rules out small ringing around 0.5 V as the explanation. Some intervals are longer, but the dominant event rate remains much faster than the oscillator's charge-time scale.

## Exact U3 extraction and theoretical scale

`original-U3-extract.cirpart` contains original library lines 196–217 unchanged: current modulation, ramp capacitor, 1.75 V comparator, 20 ns buffer delay, reset switch, ULQ multiplexer and blanking network. Original support subcircuits/models are read from the same `xyce-init` library; this oscillator does not invoke any of the altered latch or COMP IC statements.

Boundary: unloaded SYSCLK output, ULQ_MODE fixed at 0, and SDWN boundary explicitly specified per run. Full-model downstream loading/interactions are absent, so this is a subsystem diagnosis rather than a replacement full-model waveform.

Original CRAMP=7.14286 pF and charging current=5 uA±0.3 uA give a simple zero-to-1.75 V charge time of 2.500001 us at nominal current, or approximately 2.35849–2.65958 us across modulation. Reset/delay and off-state leakage modify that estimate; it is not an exact complete period. Nevertheless the observed full-model ~0.6 us median period is not explained by the ±6% current modulation alone. The early isolated ramp reaching threshold near 2.363 us is consistent with the initial +0.3 uA modulation and finite off-state leakage.

## Executed boundary and numerical contrasts

All requested runs had a 90-second ceiling; every run finished in under 0.2 seconds with exit code 1. Full logs, exact netlists and available partial waveforms are preserved.

| Boundary/initialization | Default | Tighter tolerances |
|---|---|---|
| Normal OP; SDWN=0, ULQ=0 | No DC operating point found | Same |
| Normal OP; SDWN initially1, changes to0 over1ns at1us; ULQ=0 | Stops at SDWN=0.5 boundary, t=1.0005us | Same |
| Diagnostic UIC, all-zero initial state; SDWN=ULQ=0 | Stops at2.36370372us; RAMP=1.75051225V; raw comparator reaches0.5V | Stops at2.36301069us; RAMP=1.75V |
| Same diagnostic UIC, Gear integration | Stops at2.36301067us; RAMP=1.75V | Same endpoint |

Tighter settings are `.OPTIONS TIMEINT RELTOL=1e-5 ABSTOL=1e-9` and `.OPTIONS NONLIN-TRAN RELTOL=1e-6 ABSTOL=1e-12`; Gear adds only `.OPTIONS TIMEINT METHOD=GEAR`. No device values, comparator expressions, or switch parameters changed. UIC is confined to the subsystem diagnostic and is not claimed equivalent to the full reference's normal-OP initialization.

All UIC variants fail around the **first comparator transition**, before one SYSCLK rise reaches 0.5 V. Their failure histories contain repeated timestep rejection down to approximately 1e-19 s, despite small nonlinear residuals; stricter tolerances or Gear do not establish a usable oscillator waveform. The original oscillator's lack of a simple DC equilibrium is not by itself a model defect; the more significant observation is failure to traverse the first event under the explicit transient initialization.

## Interpretation and stop point

The full-model ~1.6 MHz pulses cannot be dismissed as small-threshold ringing. The subsystem cannot yet reproduce the expected oscillator cycle under default or stricter settings. These results establish an unresolved portability/numerical-accuracy concern, not the exact source of the full-model faster pulsing. Downstream interaction, incomplete reset, or solver event handling remain hypotheses; the present full waveform lacks RAMP/raw comparator/reset signals needed to distinguish them.

Do not label the 1.5 ms run periodic steady state, and do not treat a successful return code as validation of switching frequency. Existing independently authorized BOM runs can remain recorded as diagnostic executions, with accuracy limitations explicitly carried forward. No speculative physical-parameter correction or smoothing is justified.

The most useful next evidence is a native official PSpice run of this public, original U3 extraction and the original TI reference, with RAMP, raw comparator, delayed reset, SYSCLK and SDWN plotted. Alternatively, a documented Xyce behavior correction must first pass the extracted oscillator and frequency checks before broad full-model runs are repeated. Further blind full-model duration or tolerance sweeps are not warranted by this subsystem failure.

Reproduce statistics with `python analyze.py`; `analysis.json` contains all counters, period quantiles, endpoints and waveform hashes. `runs.json`, `enable-runs.json`, `uic-runs.json`, `gear-runs.json` record execution outcomes. Every case directory retains stdout and its exact netlist; partial CSVs are kept even when failing.
