# A1 direct bootstrap implementation plan

> **For agentic workers:** use executing-plans for board integration and independently assigned simulation work; final requesting-code-review required.

**Goal:** Remove R20/R30, directly connect nearby 100nF C22/C32 between BOOT and SW, use verified 0.1% feedback MPNs without changing resistance.
**Architecture:** Local edits to authoritative routed board and native schematics; never regenerate the complete board. Sync source/BOM and add independent connection checks. Preserve historical simulation evidence.
**Tech Stack:** KiCad10.0.7 pcbnew/CLI, Python unittest/pytest, ngspice optional bounded diagnostic.
**Spec:** electronics/simulation/webench-handoff/minimal-correction-proposal.md and user explicit confirmation.

## Constraints
No push/PR/merge/manufacturing release. Preserve unrelated A1 geometry and prior uncommitted evidence. Feedback RT0603BRD07100KL / RT0603BRD0713K3L. No BOOT-to-SW copper short.

## Review focus
Wrong same-net short; leftover isolated cap; regenerated unrelated layout; false precise-MPN claim; historical failure overwritten.

## Tasks
- [x] Establish failing source topology/MPN tests and snapshot full pre-edit board/source/BOM.
- [x] Edit source and native schematics/BOM. Implement local PCB removal/cap placement/short routing; verify no unrelated geometry change.
- [x] Synchronize simulation source contracts and new versioned decks through delegated simulation task; preserve old evidence.
- [x] Run source tests, KiCad ERC/DRC/parity, BOM/pad/net checks, whole project tests; produce before/after layout views and route lengths/vias.
- [x] Independent review, fix important findings, save local commit, report remaining hardware/PVT limitations.

## Execution ledger
Ruling: continue existing dedicated a1-kicad10-validation workspace with full external baseline snapshot; user requires continued A1 work and preservation of uncommitted evidence. A new checkout would omit that evidence unless copied. No main edits.

Source contract: three intended failures recorded, then 3/3 pass after source changes. Native ERC0, XML/BOM/source cross-check pass. Project unittest154 + source3 + simulation14 + web12 + mechanical6 pass. Web has pre-existing ResourceWarning (unclosed BOM file); pytest unavailable, used actual unittest suites. Local routing delegated while main integrates metadata.

Final review finding fixed: final circuit.py placement loc overrode early c() placement. test_cap_placement_matches_reviewed_local_board RED (47,34)→GREEN (48,41.9 and97,41.9), all4 source tests pass; full suite rerun. KiCad build exit0; ERC/DRC/parity/contract0. Bounded new-model diagnostic9V/C0.8 aborted0.761902ms b2boot; dynamic remains unresolved, no extra scan or hardware pass claim.

Final independent review: no unresolved Important/Critical findings. Feedback relocation and B-channel GND via moves explicitly scoped and recorded. Same-version baseline refill audit found no >1e-6mm² polygons outside two buck windows. Current full source checks4+simulation14+project154+web12+mechanical6=190 pass. Full final build0, latest hashes agree. Local commit selected; no push/PR/merge/release.
