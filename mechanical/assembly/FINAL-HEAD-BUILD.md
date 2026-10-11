# Final 60483 head assembly source

This package describes direct assembly of the final 60483 head, repeated independently for R, L, F, and B while each arm is off the common base. It never alters the frozen mechanical model.

## Coverage and inputs

- Final arm inventory: 167 instances; four arms: 668.
- No prebuilt core or shaft input. Every component is explicitly introduced from its BOM unit. Finished motors and servos are purchased units; their internals are not disassembled.
- 88 local steps explicitly introduce 165 instances once. The two deferred interface parts are #84 (2780) then #81 (40490), introduced once after the arm seats on the base.
- The wall/motor/platform assembly is fully described using stable CORE-01…49 IDs. HEAD-FINAL-01 now introduces just the lower wall frame; the remaining original HEAD-FINAL IDs are preserved. HEAD-TT-01…09 remain lower-turntable steps.
- Wall foot pins #49/#50 are inserted into the wall before seating. Bottom connector #77 is first attached horizontally to vertical beam #78 off the base; its downward pins later enter the base along with the arm. Do not install a duplicate #77 on the base.
- The guide ledger namespaces base, support and the four arms, and assigns every one of the 882 instances a unique introduction page. Reference or whole-model views do not count as introductions.

## Assembly order

First build the three-frame wall, motor mount and platform from individual parts. Insert the guide pins before the guide frame. Install the crosshead and open-ended servo linkage before the servo. Mount the crank to the unpowered servo off the platform only under the stated independently verified pose/interface condition, then lower the pair onto the ear pins.

Then install lower turntable #34, six long pins #35–40, five short pins #42/#43/#46–48, the −Z rail #45, +Z rail #41, long pin #44, and diagonal #86, in that order. Then insert shaft #24 and fit each of #25–29 individually from +X along −X. This keeps the −Z pin/rail entry and +Z diagonal entry clear. Only then begin the head.

Build the two side panels separately. Preinsert the four turntable long pins, connect the −Z panel, and build each root with its −Z bracket, axle, outer half bush, inner full bush, jaw, and second full bush. The +Z side remains open until both inner stacks are threaded. Then fit the +Z panel and finish its brackets and half bushes.

Build the wheel jaws with the second thin beam absent during first-side shaft/pin insertion. For the jaw linkage, preinsert each 3673 pin halfway into its jaw, fit the two links independently from opposite sides, and only then connect the central crosshead/axle/outer half bushes. No pin collar is instructed to pass through an already closed pair of host bores.

Mate the head to the core and insert the 12L pushrod while the crank connection remains open. Final crank closure is conditional on an independently established matching servo pose and natural hole alignment. Stop if alignment would require forced backdrive or powered positioning. The package gives no powered calibration commands.

## Generate

Run from the project root or any directory:

    python mechanical/assembly/build_final_head.py

Useful variants:

    python mechanical/assembly/build_final_head.py --data-only
    python mechanical/assembly/build_final_head.py --render-only
    python mechanical/assembly/build_final_head.py --render-only --select 8 11 24
    python mechanical/assembly/build_final_head.py --render-only --references-only

Paths above assume the repository root; elsewhere pass the absolute script path. Sources and recipes live in `mechanical/assembly/`, generated diagrams and audits in `generated/mechanical/manual/`. Set `QUADCUBER_MECHANICAL_OUTPUT` to isolate rendering output. Use a separate checkout before regenerating authored recipe files.

## Files and schema

- `final-head-steps.json`: authoritative final-only instruction data.
- `final-head-diagrams/01.png` through `30.png`, plus `TT01.png` through `TT09.png` and `CORE01.png` through `CORE49.png`: native LDraw mesh step diagrams.
- `final-head-diagrams/opening.png`: final head near-closed (~3.8417°) and normally open (25°); both have whole-head roll 0°.
- `final-head-render-audit.json`: image hashes and exact rendered instance lists.
- `final-head-opening-audit.json`: both reference-pose geometry snapshots and image hash.
- `validate_final_head.py`: independent coverage and final-state checks.
- `final-head-validation.json`: generated validation findings.

Top-level fields: `prerequisites`, `rows`, `steps`, `validation`, `source`, and `reference_images`.

Each step includes `source_step_id`, `title`, `parts`, `image`, `instructions`, `check`, `added_part_ids`, `new_parts`, `visible_part_ids`, `highlight_part_ids`, `geometry_records`, `introduced_part_ids`, `cumulative_introduced_count`, `subassembly_id`, and `insertion_vectors_mm`.

`rows` and each geometry record use `{index1, name, color, position_ldu, rotation}`. `index1` is the exact one-based position in `candidate.module(0, 0, False, True)`, not the part type number. Position units are LDU, with 1 LDU = 0.4 mm. Each matrix preserves the frozen part orientation. Local A = +Y and B = −Y. Apply the source `ARM_ROT` for each arm; do not mirror the local instructions.

`visible_part_ids` is a local completed-state view, not the whole accumulated arm. Parts already built but outside a local view remain in their independently supported subassemblies. `introduced_part_ids` is the exact cumulative inventory. All lists are copied at step creation to preserve snapshots.

`new_parts` and `added_part_ids` exclude only the two deferred interface instances. Their union is exactly the 165 instances assembled here. Prebuilt 0 + added 165 + deferred 2 is an exact, disjoint partition of all 167 final arm instances.

## Evidence limits

All diagrams render actual final native LDraw triangle meshes. No simplified replacement geometry or image repainting is used. Image arrows indicate intended directions; they do not establish a continuous collision-free path or hand/tool access.

The 8L root axle carries a 64 mm stack: 4 + 8 + 8 + 8 + 8 + 8 + 8 + 8 + 4 mm. Nominal axial reserve is zero. Free jaw motion, half-bush retention, insertion forces, structural loads, deformation, control interlocks, and physical assembly have not been verified. None of the generated checks is physical or powered-operation approval.

The supplied geekservo mesh is approximate and marked NOCERTIFY. Its ear holes, output interface and insertion forces need physical confirmation. The crosshead axle stack is 24 mm on a 3L axle, with zero nominal axial reserve. Mechanical instructions do not supply a powered servo calibration procedure.

Repository layout note: preserve verified illustrations and PDF for ordinary builds. Full rerendering is an explicit maintenance operation in a separate checkout; it is not expected to reproduce PDF metadata byte-for-byte. The currently delivered PDF and image hashes remain frozen.
