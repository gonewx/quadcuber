# Rebuild the final assembly guide

The geometry is frozen at 882 parts. This manual explicitly introduces all 882 inventory units once, with no prebuilt core. Finished motor and servo bodies remain purchased parts. Each arm reaches165 parts off the base, then receives84 and81 after seating. The88 local pages are repeated independently for all four arms.

From the project directory:

1. python3 mechanical/assembly/finalize_source_wording.py
2. python3 mechanical/assembly/render_base.py
3. python3 mechanical/assembly/render_support.py
4. python3 mechanical/assembly/build_final_head.py
5. python3 mechanical/assembly/render_interfaces.py
6. python3 mechanical/assembly/render_braces.py
7. python3 mechanical/assembly/render_wallfoot_detail.py
8. python3 mechanical/assembly/build_manual.py

Use the bundled base-steps.json and support-steps.json as the canonical assembly inputs. If reconstructing them with recover_base.py, prepare_closed_corner.py or prepare_support.py, always run finalize_source_wording.py afterward. Native diagrams contain only the parts used by the final design. Their staged positions are explanatory nominal assembly poses, not continuous-path or physical validation.

Review the generated PDF visually, run final assembly geometry/coverage checks, and then build the website with web/build_integrated_revision.py. Current-only final-BOM.csv lists part quantities without historical comparison columns. Full final MPDs remain byte-identical to the frozen geometry manifest.

Assembly order is base, final mechanical-head subassemblies, U16 onto isolated R arm, staged165-part arms onto the base, reserved side braces, four upper stops, and130-part seat/guide structure. Keep the crank/link connection open during pushrod insertion. Keep independent support and power disconnected throughout. The jaw's zero stroke is approximately3.8417 degrees;25 degrees is its normal opening maximum. Whole-head roll0/50/90 degrees is separate.

The external handle must remain pressed to hold the seat up. Physical retention, insertion access, self-return, load, impact, hand isolation and powered safety are not certified.

Repository layout note: preserve verified illustrations and PDF for ordinary builds. Full rerendering is an explicit maintenance operation in a separate checkout; it is not expected to reproduce PDF metadata byte-for-byte. The currently delivered PDF and image hashes remain frozen.
