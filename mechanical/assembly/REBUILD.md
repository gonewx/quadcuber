# Rebuild the final assembly guide

The approved R5 lower-frame revision has 938 parts. This manual explicitly introduces all 938 inventory units once, with no prebuilt core. Finished motor and servo bodies remain purchased parts. Each arm reaches165 parts off the base, then receives84 and81 after seating. The88 local pages are repeated independently for all four arms.

From the project directory:

1. python3 mechanical/assembly/build_base_stiffening_steps.py
2. python3 mechanical/assembly/render_base.py
3. python3 mechanical/assembly/render_support.py
4. python3 mechanical/assembly/build_final_head.py
5. python3 mechanical/assembly/render_interfaces.py
6. python3 mechanical/assembly/render_braces.py
7. python3 mechanical/assembly/render_wallfoot_detail.py
8. python3 mechanical/assembly/build_manual.py

Use the bundled base-steps.json and support-steps.json as the canonical assembly inputs. Do not run the historical recover_base.py or prepare_closed_corner.py over the R5 recipe; use build_base_stiffening_steps.py. The unchanged head recipe and images do not need rerendering for this revision. Native diagrams contain only the parts used by the final design. Their staged positions are explanatory nominal assembly poses, not continuous-path or physical validation.

Review the generated PDF visually, run final assembly geometry/coverage checks, and then build the website with web/build_integrated_revision.py. Current-only final-BOM.csv lists part quantities without historical comparison columns. Final MPDs reproduce the R5 release manifest; the R4 provenance remains historical.

Assembly order is base, final mechanical-head subassemblies, U16 onto isolated R arm, staged165-part arms onto the base, reserved side braces, four upper stops, and130-part seat/guide structure. Keep the crank/link connection open during pushrod insertion. Keep independent support and power disconnected throughout. The jaw's zero stroke is approximately3.8417 degrees;25 degrees is its normal opening maximum. Whole-head roll0/50/90 degrees is separate.

The external handle must remain pressed to hold the seat up. Physical retention, insertion access, self-return, load, impact, hand isolation and powered safety are not certified.

Repository layout note: preserve verified illustrations and PDF for ordinary builds. Full rerendering is an explicit maintenance operation in a separate checkout; it is not expected to reproduce PDF metadata byte-for-byte. The currently delivered PDF and image hashes remain frozen.

After model/inventory and manual rebuilds run `python tools/record_mechanical_release.py`, then `python tools/build_distribution.py`. R4 PROVENANCE.json and layout-baseline.json remain historical; release.json records explicitly updated mechanical assets.
