# Targeted cold-start differential diagnosis

Three controlled Linux Xyce 7.10 runs are complete. They narrow the unresolved failure to the first switching event from the cold reference's near-zero-energy state; they do not validate cold startup. No repository, PCB, original TI library, or solver source was changed. Every run reads the same existing `TPS54302_TRANS.xyce-init.LIB`, SHA-256 `47f1df44d7467c19c63eedf896bb61e2061eb455c65938f05a43e12819f812e7`, and the same two-level alias. No UIC, physical parameter adjustment, comparator smoothing, or new numerical settings were introduced.

## Restored factory-reference differences

The inputs are locally reconstructed from the original DSN and trans.sim, not a Cadence-exported netlist. Inspection of both `xyce-reference/*/init-compatible-driver.cir` gives:

| Item | Startup | Steady_State |
|---|---|---|
| Chip STEADY_STATE | 0 | 1 |
| VIN | PULSE 0→12 V, delay 100 us, rise/fall 10 us | DC 12 V |
| Output load | R=5/3 ohm | DC current sink 3 A |
| Inductor | 10 uH, DCR 10 mohm, IC=0 A | Same L/DCR, IC=3 A |
| BOOT–SW capacitor | 0.1 uF, IC=0 V | Same C, IC=12 V |
| Two output capacitors | Each 22 uF, ESR 2 mohm, IC=0 V | Same C/ESR, IC=5 V |
| Explicit VOUT IC | None | 5 V |
| Analysis | Stop 6.5 ms, print from 0, maxstep 20 ns | Stop 800 us, print from 750 us, maxstep 20 ns |
| Other components | Feedback 100k/13.3k, series 49.9 ohm, feedforward 75 pF; VIN 10 uF+0.1 uF; EN divider 510k/105k | Same values/connectivity |
| Anonymous feedback junction | N16776600 | N16785508 (name-only difference) |

The load difference is physically material: at 0 V, the resistor draws 0 A but the current sink still requests 3 A. Thus the successful Steady_State reference cannot be interpreted as a cold-start run with merely a different chip flag.

## What STEADY_STATE actually changes

Exactly four occurrences beyond the subcircuit declaration exist in the original model:

1. Lines 181–182: amplitude of a 200 us pulse at U10_N16864604, with 1 ns edges. Through OR gates U617→U622→U615 (148–161), this drives switch U10_S2 (147), which discharges hiccup timing node U10_N16864691. It is a temporary hiccup timing override, not a blanket bypass of shutdown.
2. Lines 249–250: VREF_GM is fixed at 0.6 V if STEADY_STATE>0.5; otherwise it follows SS_TR capped at 0.6 V.
3. Line 257: soft-start capacitor C_U4_C9 starts at `1.7*STEADY_STATE` V.
4. Original line 366: COMP starts at `1.3695*STEADY_STATE` V. Existing normal-OP compatibility candidate applies the same initial value to its zero-volt-source-connected node N16888001.

All four are a bundled parameter change. None changes the shutdown input directly or the power-stage R/L/C values. The cold-test trace with flag=1 confirms that SS_TR initially equals 1.7 V but is discharged by the unchanged shutdown network while VIN is zero; by about 43.72 us it is already below 1 mV. VREF_GM remains forced to 0.6 V nonetheless.

## Chosen runs and results

Each driver has one scientific change relative to its indicated reference. Common instrumentation changes are an absolute alias include, printing additional internal nodes, and a bounded 0–800 us observation window with the same 20 ns maximum step. Startup's original 6.5 ms is deliberately not claimed complete. Full reversible diffs are in each `driver.patch`. Per-run timeout was 110 seconds; actual runtimes were 1.42, 0.16 and 36.64 seconds.

| Case | Single scientific change | Observed result |
|---|---|---|
| startup_state1 | Startup chip flag 0→1 | Exit 1, timestep too small; last point 108.133086 us; VOUT≈1.137 uV |
| startup_dc12 | Startup VIN pulse→DC 12 V | Exit 1, timestep too small; last point 2.38699189 us; VOUT≈1.354 uV |
| steady_state0 | Steady_State chip flag 1→0 | Exit 0, reaches 800 us; 61,330 rows; VOUT=0.749525 V at end, not a regulated-5-V pass |

The original candidate Startup stopped at 108.133711 us. Flag=1 shifts that endpoint by only 0.625 ns despite different VREF/COMP initialization.

For the two failing variants, the first accepted SW rise above 1 V occurs at 108.132338 us and 2.38624390 us respectively. Their last accepted samples are **0.748000 ns and 0.747990 ns after that first rising-edge sample**. These are sampled-event offsets, not exact physical crossing times. Shutdown passed below 0.5 earlier: approximately 105.70 us and 1.864 ns respectively. Both traces therefore progress beyond the shutdown threshold and fail almost immediately after their first high-side switching event.

The successful `steady_state0` case demonstrates that flag=0 and soft-start following logic can be integrated for hundreds of switching events (423 observed SW rises) when the external circuit starts precharged. Its VREF_GM reaches only 0.0861902 V by 800 us; VOUT follows the soft-start regime rather than staying at 5 V. It begins at VOUT=5 V / IL=3 A, falls to a minimum -0.198851 V with the still-active 3 A sink, and then rises. This waveform is diagnostic evidence, not a physically accepted cold-start substitute.

## Supported inference and limits

* Neither forcing STEADY_STATE=1 nor removing the VIN ramp resolves cold-reference failure.
* STEADY_STATE=0 alone does not make the solver fail: the precharged reference completes with it.
* The common cold failure is associated with the first SW rise from near-zero output and inductor energy, rather than exclusively with the immediate SDWN=0.5 crossing.
* External precharge and load type remain confounded between reference families. These three runs do not identify which particular stored-energy element or equation causes the first-edge failure. A claimed device defect, an altered diode ideality, or a smoothing workaround would be unsupported.

## Stop point and next required evidence

Stop this compatibility branch after these three discriminating runs. The factory Startup reference has still not completed; do not count the completed precharged diagnostic as a startup pass. Separately authorized real-BOM preinitialized steady-state and load-step tests are outside this cold-start diagnosis and may proceed independently; their completion does not resolve this cold-start gate. No additional blind solver-option sweep or physical-model modification is justified by this evidence.

The decisive next evidence is a **native, official PSpice execution of the original TI Startup DSN/trans.sim and original model**, providing its exported netlist, warnings, and first-switch waveforms (VIN, EN, SDWN, SW, inductor current, COMP, SS_TR and bootstrap voltage). The library identifies PSpice 16.2 as its development simulator. This work does not establish availability, licensing, or Linux support of any current vendor edition; it has not installed or opened a new licensed environment. An already authorized official vendor environment or vendor-supplied reference result would address the missing oracle.

A permissible read-only online follow-up is checking public TI/Cadence model release notes, documented PSpice initialization behavior, and a vendor-published cold-start result for this exact model revision. Public documentation may identify known compatibility issues but cannot itself supply an unobserved native execution result. Only generic/public model identifiers and error signatures would be needed for searches; no real BOM parameters, design files or private traces need be uploaded.

## Reproducible evidence

* `results.json`: actual return codes, requested stop, first/last samples, ranges, elapsed time and model/alias hashes.
* `summary.json`: file hashes, first SW rising sample and endpoint offsets.
* Each case directory: unchanged-read model references, driver, exact patch, stdout log, full CSV waveform, final ten samples.
* `transitions.json`: selected event crossings for the cold variants.
* `differential.png`: overview of VOUT, reference voltage and first-edge failure alignment.
* `run_differential.py`: exact three-run generation/execution; `summarize.py`: independent CSV summarization and plot generation.
