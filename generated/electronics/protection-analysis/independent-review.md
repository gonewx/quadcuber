# Independent protection-boundary review

2026-10-12. Read-only review of the script, status, report and emitted CSV data; this reviewer did not rerun all ngspice cases and did not change the PCB. No TI vendor model or hardware result is inferred.

## Checked outcome

- 48 input-RLC and 60 regenerative-energy rows are present. Maximum fuse-path current is 199.972799 A and maximum startup integral is 1.567335927 A²s. The integral uses the series cable-inductor current, hence the F1 path; it does not substitute PSU regulator current for output-capacitor discharge current.
- The 12 cases with 151.5 Ω and energy ≤0.05 J/event have maximum VM 11.2035285 V and zero modeled TVS energy. Maximum absolute energy balance residual over all energy cases is 0.001518379 J.
- Rechecked waveform column selection and signs: regeneration and source-hold currents inject energy; TVS and bleed consume energy; the capacitor term uses final-minus-initial stored energy. No column/sign error found.
- An independent instantaneous-energy upper bound at 2256 µF is sqrt(9.18²+2×0.05/0.002256)=11.340134 V. Discharge through 151.5 Ω to 9.18 V takes 72.226 ms. At 5 Hz with maximum pulse width 100 ms the off-window is 100 ms. Thus this conservative calculation supports resetting below the chosen baseline between events, beyond the script's five-event sample, **under the explicitly modeled bounds**.
- A guaranteed minimum bus load addresses repeated charge accumulation when all other loads may be absent. Two 300 Ω / 1 W bleeders are consistent with that purpose. They do not establish an operating envelope for the actual robot until returned mechanical energy and temperatures are measured.

## Limits that must remain visible

The reported 199.97 A pulse is possible in this model because the charged PSU output capacitor lies outside the ideal 6.5 A regulator-current limit. This is not an arithmetic contradiction. The small ratio to nominal fuse melting I²t alone does not qualify connectors, switch bounce, MOSFET transient SOA, ideal-diode controller startup or fuse life. The report correctly retains these limitations; no mathematical need to add an NTC solely from the pulse's peak has been demonstrated.

The 1 J and other out-of-envelope rows are rejected, not used to qualify repetitive SMBJ dissipation. The static piecewise-linear TVS has no junction-temperature or lifetime model. The 600 W data-sheet headline is not applied as a general energy limit. The 150 Ω normal-operation result avoids modeled TVS avalanche within the chosen ≤0.05 J/event, ≤5 Hz, 5–100 ms bounds; it does not remove layout-induced inductive spikes or component spread outside those bounds.

No must-fix numerical or sign error found in the reviewed results. The report's rounded instantaneous upper bound should be 11.34 V. No manufacturing release, actual PSU acceptance, actual motor-energy verification, vendor-model validation or physical thermal pass follows from this review.

## Reviewed artifact SHA-256

- `electronics/simulation/run_protection.py`: `234a125f7a5c497458d2b3d56e37ea94af55377d9b6cca30509c886299a7e6e0`
- `generated/electronics/protection-analysis/input_rlc.csv`: `1085b5761224da57412c9edd88622d4c7f03366440698c7fd2a873c9bcba8297`
- `generated/electronics/protection-analysis/regenerative_energy.csv`: `1bba1d382d78bc3a0613c6f82cfff8900048b5aaed03addcbb75dab77403d6da`
- `generated/electronics/protection-analysis/run-status.json`: `c0da6cf7a09e2f7c0cad97fa2afc3da94c148306394f51f8aea1da85563d031f`
