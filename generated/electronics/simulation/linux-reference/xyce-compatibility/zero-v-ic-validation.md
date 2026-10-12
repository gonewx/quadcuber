# Zero-volt-source IC relocation: observed limits and normal-OP justification

**Conclusion: acceptable as a clearly labeled normal-OP compatibility candidate preserving the model's intended voltage initial condition. Not acceptable as a claim of byte-identical model execution, UIC equivalence, or equivalence across arbitrary hierarchy.** No TI model or solver sources were modified by this investigation.

## Independent source and matrix findings

The full-reference `Startup/Failed_Matrix1.mm` has dimensions 560 x 560 and 1,383 stored entries. Its **only all-zero row is zero-based row 9**, named `x_u1:xcore:comp` by `node-names.txt`. That row contains one stored entry, column 28 with value 0, and **no structural diagonal entry**. These facts were independently parsed and are recorded in `zero-v-ic-detailed-validation.json`.

Xyce source `/workspace/tools/src/xyce-7.10/src/NonlinearSolverPKG/N_NLS_NOX_AugmentLinSys_IC.C:138-160` reads the diagonal, clears each eligible IC row, and sets the corresponding temporary diagonal value to 1; line 164 calls replaceDiagonal. Replacing an absent structural diagonal does not create the needed entry here; the resulting row is zero.

The original TI library has `V_V1 N16888001 COMP 0Vdc` at line 258 and `.IC V(COMP)={STEADY_STATE*1.3695}` at line 366. N16888001 has capacitor/resistor/diode connections (218-228), while COMP connects electrically through that zero source and otherwise serves as a control voltage (265,295,303). The ideal source imposes `V(N16888001)=V(COMP)`. No other occurrence of V_V1 or branch-current reference to it exists in this library.

A separate hierarchy-sensitive coloring defect is relevant and must not be hidden:

* `LinearAlgebraServicesPKG/N_LAS_Builder.C:211-255` documents and implements exclusion of voltage nodes connected to independent voltage sources from IC enforcement using its source-node coloring list.
* `TopoManagerPKG/N_TOP_SerialLSUtil.C:739-742` and `N_TOP_ParLSUtil.C:1644-1647` locate the **first** hierarchy separator, then test whether the next character is V/v to recognize voltage sources. This recognizes the test's top-level and one-level source names, but fails for two-level `XTEST:XCORE:VZERO`, whose first separator is followed by X.
* Consequently, the top-level and one-level probes ignore the voltage-source-adjacent IC under normal OP, whereas the two-level probe enters the IC enforcement path and exposes the absent-diagonal failure. This matches the full reference's `X_U1:XCORE` nesting.

## Minimal RC evidence

All probes retain a 1 V supply through 1 kohm into capacitor node A (1 uF), an unchanged zero-volt source from A to observation-side B, and an unloaded E-source output. The two-level probe uses nonlinear observation `OUT=V(B)**2`, which does not load either node. The requested initial value is 0.25 V. The expected charge trajectory after applying that value is `1-0.75*exp(-t/1ms)`.

| Probe | Result |
|---|---|
| Top-level normal OP, IC A or IC B | Both finish at constant 1 V, ignoring the requested 0.25 V; this is not a passing IC test |
| One-level normal OP, IC A or IC B | Same ignored-IC behavior |
| Two-level normal OP, IC B | Exit 1; three singular-matrix warnings; DC operating point fails |
| Two-level normal OP, IC A | Exit 0; all 1,001 samples A=B exactly; A(0)=B(0)=0.25 V; max analytic error 7.48000e-7 V; A(1ms)=B(1ms)=0.724090166 V |
| Top-level UIC, IC A | A starts at 0.25 V; B's t=0 output is 0 V, then follows A; expected initialized RC curve |
| Top-level UIC, IC B | A starts at 0 V; B alone is set to 0.25 V at t=0; both then follow the zero-initialized capacitor curve, ending at 0.632120406 V |

The UIC cases are a deliberate retained counterexample: identical algebraic voltage constraints do **not** imply identical Xyce skip-OP initialization. Both sides are equal at every positive-time sample, but the capacitor's initial charge differs. Therefore these results do not authorize using the relocation with UIC.

## Scope of the acceptable candidate

For the existing two-level normal-OP reference only, changing the IC **target** from COMP to N16888001 while keeping the exact same value enforces the original intended voltage on both ends of the unchanged zero-volt source. The local RC evidence demonstrates both intended initial voltage and the subsequent energy-storage trajectory. It supports trying an explicitly named `candidate-equivalent-init` copy after preserving the failed original-target evidence.

Keep the four separately proven equals-sign syntax repairs, all original device parameters, zero-voltage source, node connectivity, XOR, switch transfer, and normal-OP analysis. Do not enable UIC, silently flatten hierarchy, claim validation of the full reference waveform, or present this as an unchanged original model. Full-reference convergence and behavior remain separate gates.

## Solver-fix follow-up

Two independent Xyce issues deserve a future focused patch and regression suite: recognize voltage-source device type reliably independent of hierarchy; and ensure IC row enforcement can supply a structural diagonal or reject unsupported sparse structure explicitly. A proposed zero-valued structural-diagonal insertion in graph construction adds no physical conductance, but still needs validation of matrix graph/device registration, row ordering, serial/parallel behavior and all IC paths. Correcting source coloring alone may cause these ICs to be ignored instead of applied. These interactions mean a broad custom solver patch is not yet a stronger immediate validation basis than the one-target, normal-OP compatibility candidate.

Files: `zero-v-ic-detailed-validation.json`, `validate_zero_v.py`, and every original probe, CSV and stdout log under `runs/zero_v_ic/`. The original four top-level run records are separately preserved in `zero-v-ic-validation.json`. No failed or contradictory evidence was discarded.
