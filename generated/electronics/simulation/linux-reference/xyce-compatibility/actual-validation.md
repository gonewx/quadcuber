# Actual numerical validation: Xyce 7.10.0-opensource

The existing 18 recorded runs (15 default probes plus 3 HSPICE-math controls) were checked numerically, not merely by exit code. A nineteenth observation-only run resolves one initial-output discrepancy. All original netlists, model files, CSVs and logs are preserved. SHA-256 values and equality between prepared and executed netlists are in `actual-validation.json`; checks are reproducible with `python validate_actual.py`.

## Results

| Check | Numerical result | Conclusion |
|---|---|---|
| Original XOR, explicitly parenthesized XOR, Boolean `!=` | Each default run matches all 9 expected points exactly; all three numeric CSV tables identical | Keep TI's original XOR under default Xyce |
| `-hspice-ext math` negative control | Both caret forms disagree with XOR at 7/9 points; parenthesized and original remain identical; `!=` matches all 9 points | Do not use math/all on original TI model |
| Single/double AND/OR, IF, E/G VALUE | All 9 input pairs have exactly expected outputs, max error 0 | Native tested syntax supported |
| Continuous VSWITCH | All 19 points match log-cubic resistance law; max relative current error 3.25743e-9 | Original continuous switch behavior retained |
| Normal OP without IC | All 1,001 samples OUT=1 V exactly | OP initialization confirmed |
| Normal OP with IC | OUT starts exactly 0.25 V; max analytic error 7.48000e-7 V | Explicit IC retained during OP-assisted transient |
| UIC/NOOP with IC | Each starts exactly 0.25 V; max analytic error 3.74834e-7 V | Both skip-OP forms preserve IC |
| UIC/NOOP without IC | Each starts exactly 0 V; max analytic error 4.99278e-7 V | Skip OP confirmed |
| UIC versus NOOP | 1,009 rows per case, exact numeric equality both with and without IC | Equivalent on this RC test |
| IC formal-pin alias, whitespace versus compact | Both 1,008-row numeric tables identical. EN(0)=0; COMP(0)=1.3695 V; max analytic errors 4.99278e-7 V and 6.87063e-7 V | Original `V(EN )` whitespace and formal-to-actual aliases work |
| Original `.IC V(Qint) {VSS}` | Exit 1, cannot convert `(`, `)` and empty string to double; erroneous nodes X1:V and X1:{VSS} ignored | Concrete syntax incompatibility |
| `.IC V(Qint)={VSS}` | Exit 0; direct Qint observation gives exactly 0.25 V at t=0 and analytic-decay error at most 1.25176e-7 V | Equals-only correction implements intended IC |

## Explicitly retained initial-output discrepancy

The original `ic_with_equals.cir` prints only an E-source-derived output, OUT, not the initialized storage node Qint. At t=0, the CSV contains OUT=0 V rather than the expected 0.25 V. The all-sample output-only check therefore **fails** with maximum error 0.25 V; `all_expected_checks_pass` is deliberately false in the JSON. No t=0 sample was silently discarded.

To diagnose this, `runs/default/ic_with_equals_observe/ic_with_equals_observe.cir` adds only `V(X1:Qint)` to the existing PRINT list. Its circuit equations, parameters, IC and analysis remain identical to the original probe, as checked programmatically. This run exits 0 and shows:

| Time | Derived OUT | Storage Qint |
|---|---:|---:|
| 0 | 0 V | 0.25 V |
| 1 us | 0.249750250 V | 0.249750250 V |
| 1 ms | 0.0919698986 V | 0.0919698986 V |

Qint matches the analytic solution `0.25*exp(-t/1ms)` across **all 1,009 samples**, with maximum absolute error 1.25176e-7 V. OUT equals Qint exactly at all 1,008 positive-time samples. Thus the intended storage-node initial condition is applied; the zero-time derived algebraic output is not initialized consistently under this UIC setup. This is a real output-initialization limitation to account for when inspecting t=0 traces, not a reason to change device parameters or remove initial conditions.

CSV output includes a t=0 row in these actual runs, despite older source comments mentioning absent t=0 PRN output. Actual observations take precedence over those comments.

## Evidence and justified action

* `runs/results.json`: original 18 commands and exit statuses; only `ic_no_equals` fails.
* `actual-validation.json`: every numeric check, switch point, failed output-only expectation, observation follow-up, and prepared/executed netlist hash.
* `runs/default/ic_no_equals/stdout.log`: concrete parser failures.
* `runs/default/ic_with_equals_observe/stdout.log` and `.cir.csv`: direct proof of correctly initialized Qint.
* `validate_actual.py`: standard-library numeric verification; it does not launch a solver or modify netlists/models.

This supports only a syntax-preserving correction of the original model's four `.IC V(Qint) {VSS}` statements to `.IC V(Qint)={VSS}` after retaining the failed unchanged-reference attempt. Keep the original XOR, E/G sources, switch models, node aliases, whitespace, physical parameters and initial values. The tests do not establish full-model convergence, a valid factory-reference waveform, or independent agreement with PSpice. The full reference still precedes the requested real-BOM nine-case sweep.
