# A1 exact-MPN / package / rating independent audit

2026-10-12 direct-boot-precision-v1更新：R20/R30已从装配BOM删除；R21/R31改为[RT0603BRD07100KL](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD07100KL)，R22/R32改为[RT0603BRD0713K3L](https://yageogroup.com/component-documentation/download/specsheet/RT0603BRD0713K3L)。两者分别100k/13.3k、0.1%、±25ppm/°C、0603，0.1W@70°C、75V。下文RC系列49.9Ω/反馈1%编码审查属于修订前记录，不再代表这六个位号的当前装配。当前实物匹配见新版BOM和boot-direct-revision/cross-check.json；未作库存或量产资格承诺。


2026-10-12. Read-only design audit by the independent review agent, with separate capacitor and connector/passive reviews. No PCB, netlist, purchasing record or simulation was changed by this audit. This is a component-evidence review, **not manufacturing release or a physical qualification**.

Reviewed snapshot: `electronics/circuit.py` SHA-256 `ddf27f40ea126ae153b21c24ad23e0e14e27026af6315bbed6588c31c7b12a10`; `generated/electronics/bom-grouped.csv` SHA-256 `f278c39bfe609cdc7e4491662a55bae05b9145589acc3009f5d54fa8e877af60`. The implementation owner may revise these files in response; findings below refer to these exact inputs, not an assumed later build.

## Findings requiring resolution

1. **C20/C30/C101/C121/C141/C161: `GRM32ER71E106KA12L` lacks exact manufacturer evidence.** The verified 10 µF / 25 V / X7R / ±10% / 1210 orderable family is **`GRM32DR71E106KA12L`**, with D rather than E in the size code. [Murata exact family page](https://www.murata.com/en-us/products/productdetail?partno=GRM32DR71E106KA12K) lists L/K packing; dimensions 3.2±0.3 × 2.5±0.2 × 2.0±0.2 mm. Correct the exact MPN or supply evidence for the E part. The D part retains the existing 1210 nominal lands; DC-bias effective capacitance still needs its own bound.
2. **F10–F13 `MF-MSMF110-2` is a historical 6 V part, not a fabricated part number, but is absent from the current manufacturer table.** Channel lifecycle evidence reports obsolete; no original end-of-life date notice was located. Prefer **`MF-MSMF110/16X-2`**, explicitly in the [current Bourns table](https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf): 16 V, 1.1 A hold / 2.2 A trip at 23°C, 100 A maximum fault current, Style 2. Do not substitute old `/16-2` merely because it exists; channel evidence marks that version NRND. Style 2 land verification is discussed below.
3. **MLCC lifecycle items:** original Murata public indices flag `GRM155R61A105KE15D` Last Time Order; `GRM21BR61A475KA73L` To be discontinued; `GRM1885C1H750JA01D` NRND. Their electrical values and package sizes match the design, but new-build sourcing should select current replacements. Exact final-order dates have not been established; do not invent dates from search snippets.
4. **EV3 connector remains a manufacturing HOLD.** The drawing establishes nominal hole geometry, not a manufacturer MPN, full pin numbering, observation side or current capability. This audit does not convert the provisional connector into a verified production component.

## Protection, power and connectors

| Exact MPN / references | Manufacturer evidence and package result | Status / limits |
|---|---|---|
| `0407008.WR`, F1 | [Littelfuse 407 original data sheet](https://www.littelfuse.com/assetdocs/littelfuse-fuse-407-datasheet?assetguid=b3bb718b-1fde-4cdc-9cb1-a6465c126ec4): 1206, 8 A, 24 VDC, 60 A interrupt with specified circuit time constant; nominal melting I²t 24.12 A²s. Custom 407 footprint replaces the erroneous prior 467 selection. | Exact part/rating verified. Time-lag fuse is not fast semiconductor protection. 5 A continuous system budget and current-limited 9 V source remain necessary. |
| `CSD18540Q5B`, Q1 | [TI original data sheet](https://www.ti.com/lit/ds/symlink/csd18540q5b.pdf): 60 V N-MOS, 5×6 mm SON, gate ±20 V; RDS(on) max 3.3 mΩ at VGS 4.5 V and 25°C. KiCad's exact CSD18540Q5B symbol explicitly selects TDSON-8-1; footprint pads 1–3 source, 4 gate and merged 5 drain agree with source. | Package/pin assignment verified; room-temperature RDS(on) is not a hot-loss bound. Generic KiCad land is not claimed to reproduce every TI recommended dimension. |
| `LM74700QDBVRQ1`, U4 | [TI original data sheet](https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf): DBV six-pin package; 1 VCAP, 2 GND, 3 EN, 4 CATHODE, 5 GATE, 6 ANODE. Source connects these correctly. | Verified; EN does not disconnect forward power. Reverse blocking does not absorb motor regeneration. |
| `TPS54302DDCR`, U2/U3 | [TI original data sheet](https://www.ti.com/lit/ds/symlink/tps54302.pdf): DDC SOT-23-6, 4.5–28 V input, 3 A nominal output; 1 GND, 2 SW, 3 VIN, 4 FB, 5 EN, 6 BOOT. | Package/pins verified from original reference review. Current label is not board thermal qualification. Vendor transient-model execution remains blocked, independently of this audit. |
| `DRV8871DDAR`, U10–13 | [TI original data sheet](https://www.ti.com/lit/ds/symlink/drv8871.pdf): DDA PowerPAD SOIC-8, 6.5–45 V operating range. 1 GND, 2 IN2, 3 IN1, 4 ILIM, 5 VM, 6 OUT1, 7 PGND, 8 OUT2, EP ground. | Verified mapping/package. 43.2 kΩ limits short-term current approximately 1.48 A; this is not continuous motor/PCB thermal approval. Initial 0.75 Arms target requires measurement. |
| `SMBJ12A`, D3; `SMBJ12CA`, D4 | [Littelfuse SMBJ original table](https://www.littelfuse.com/assetdocs/tvs-diodes-smbj-series-datasheet?assetguid=ba555e99-a12d-4f72-a0b6-86b06c67171e): SMB/DO-214AA; VRWM 12 V, breakdown 13.3–14.7 V at 1 mA, rated pulse clamp 19.9 V at 30.2 A. A unidirectional cathode to VM; CA bidirectional input. | Verified package/polarity. 600 W is a specified nonrepetitive waveform rating, **not** general continuous/repetitive braking capacity. |
| `SS14-E3/61T`, D2/D5 | [Vishay SS12–SS16 original data sheet](https://www.vishay.com/docs/88746/ss12.pdf): SS14 40 V / 1 A, SMA DO-214AC, cathode band; /61T reel packing. Both source cathodes connect VSYS. | Verified. Reverse leakage is nonzero and temperature dependent; do not describe diode OR as zero-leakage galvanic isolation. |
| `CRCW2512300RFKEG`, R500/R501 | [Vishay original 20035](https://www.vishay.com/docs/20035/dcrcwe3.pdf): 2512, 300 Ω, F ±1%, K temperature coefficient and EG packing; standard 1 W size rating. | Verified code/size/power. Two parallel parts give 150 Ω, about 0.562 W total at 9.18 V. The tested ≤0.05 J/event and ≤5 Hz envelope is model-specific, not a full-power brake. Film temperature and pulse curve still govern. |
| `SRP1245A-100M`, L1/L2 | [Bourns original data sheet](https://www.bourns.com/docs/Product-Datasheets/SRP1245A.pdf): 10 µH ±20%, Irms 9 A at 40°C rise, Isat 16 A at 20% inductance drop, DCR max 25.5 mΩ. Lands: outer span 14.2, inner gap 8.0, width 5.0 mm agree with custom footprint. | Electrical and lands verified. Do not treat Isat and Irms as interchangeable. Body/courtyard arrow interpretation was not re-qualified photographically in this pass; no definite mismatch established. |
| `RASPC722X`, J1 | [Local source/geometry review](raspc722x-review.md): Switchcraft DC jack; parent visually checked original drawing, 5 A carrying / 24 V, mating 762/762Z 5.5/2.1 mm. Original PDF pending local archive. | Center-positive regulated 9 V, <=5 A budget; recommended plated slots, unused sleeve shunt. Native checks do not certify loaded temperature or physical fit. |
| `61300211121`, `61300311121`, `61300411121` | [Würth 2-pin](https://www.we-online.com/components/products/datasheet/61300211121.pdf), [3-pin](https://www.we-online.com/components/products/datasheet/61300311121.pdf), [4-pin](https://www.we-online.com/components/products/datasheet/61300411121.pdf): 2.54 mm pitch, 3 A, nominal hole 1.10±0.15 mm. | Present 1.0 mm drill is inside published range; not a mandatory board-change finding. Check finished-hole tolerances with fab. |
| `MF-MSMF050-2`, F2/F3 | [Bourns original table](https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf): 1812 Style 1, 15 V, hold/trip 0.5/1.0 A, 100 A fault rating; hold current 0.44/0.37/0.29 A at 40/60/85°C. | Exact model remains in table; no confirmed lifecycle blocker found in this pass. Nominal 0.5 A is not an all-temperature continuous budget. |
| `MF-MSMF110-2`, F10–13 | Current Bourns table lacks old 6 V model; replacement `/16X-2` listed above. | Must resolve MPN and Style 2 land confirmation before release. |
| `USB4105-GF-A`, J5 | [GCT manufacturer drawing](https://gct.co/files/drawings/usb4105.pdf), referenced by exact standard KiCad USB4105-xx-A footprint; prior independent A1 review checked connector implementation. | Retained prior verified package mapping. This pass did not obtain a fresh readable drawing; do not count this row as a new dimension-by-dimension inspection. |
| `UNCONFIRMED user drawing`, J10–13 | [Local drawing review](ev3-user-drawing-review.md). | HOLD: exact MPN, physical pin numbering/view, contact ratings, mating and ear clearance. Not Adafruit4434 by assumption. |

### PTC land qualification detail

Current generic 1812 copper has pads 1.125 × 3.4 mm, centres ±2.1375 mm, inner gap 3.15 mm. Bourns Style 1 recommended drawing lists 1.68 / 3.1 / 2.95 mm; Style 2 lists 1.5 / 3.2 / 2.7 mm. Text extraction cannot establish the latter arrows' orientation. The likely Style 2 interpretation is pad 1.5 × 3.2 mm, inner gap 2.7 mm, centres ±2.1 mm, but **this is explicitly an interpretation pending visual confirmation**, not a proven exact land. `/16X` body dimensions A 4.37–4.83, B 3.07–3.41, C 0.35–0.80, D 0.30–1.20, E 0.20–0.65 mm are directly tabulated. A local pad enlargement at effectively unchanged centres may avoid rerouting; only do so after confirming arrows and DRC. A land-pattern difference alone is not proof that the present solder joint is impossible.

## Capacitors: exact manufacturer entries

| Exact MPN | Nominal rating / package | Result |
|---|---|---|
| [GRM155R71C104KA88D](https://pim.murata.com/en-us/pim/details/?partNum=GRM155R71C104KA88%23) | 100 nF 16 V X7R 0402 | Match |
| [GRM155R61A105KE15D](https://pim.murata.com/en-us/pim/details/?partNum=GRM155R61A105KE15%23) | 1 µF 10 V X5R 0402 | Match; lifecycle flag above |
| [GRM21BR71C105KA01L](https://www.murata.com/en-us/products/productdetail?partno=GRM21BR71C105KA01%23) | 1 µF 16 V X7R 0805 | Match |
| [GRM21BR61A475KA73L](https://pim.murata.com/en-us/pim/details/?partNum=GRM21BR61A475KA73%23) | 4.7 µF 10 V X5R 0805 | Match; lifecycle flag above |
| [GRM1555C1H150JA01D](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM1555C1H150JA01-01A-EN_PDF_CERAMICCAPACITORSMD) | 15 pF 50 V C0G 0402 | Match |
| [GRM21BR71H104KA01L](https://pim.murata.com/en-sg/pim/details/?partNum=GRM21BR71H104KA01%23) | 100 nF 50 V X7R 0805 | Match |
| GRM32ER71E106KA12L | Claimed 10 µF 25 V X7R 1210 | Exact-MPN evidence missing; use verified D-code candidate above |
| [GRM32ER71E226KE15L](https://ds.murata.com/simsurfing/mlcc.html?oripartnumbers=%5B%22GRM32ER71E226KE15L%22%5D&partnumbers=%5B%22GRM32ER71E226KE15%22%5D) | 22 µF 25 V X7R 1210, max thickness 2.7 mm | Match |
| [GRM1885C1H750JA01D](https://pim.murata.com/en-global/pim/details/?partNum=GRM1885C1H750JA01%23) | 75 pF 50 V C0G 0603 | Match; NRND |
| [EEU-FR1E471](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1E471) | 470 µF 25 V, D10 × H12.5 mm, pitch 5 mm; 1290 mArms at 100 kHz, 43 mΩ | **Current D10/P5 footprint correct.** Do not change from memory to D8/P3.5. |
| [EEU-FR1A471](https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1A471) | 470 µF 10 V, D8 × H11.5 mm, pitch 3.5 mm; 950 mArms at 100 kHz, 56 mΩ | **Current D8/P3.5 correct; default DNP.** |

Some Murata detail pages refused full-body access while their original public index/SimSurfing content was accessible. Evidence level is disclosed; exact lifetime dates and DC-bias curves were not inferred from generic family names. Capacitance tolerance, bias, aging and temperature must be applied to the regulator's effective-capacitance requirement; a printed 22 µF is not a guaranteed operating 22 µF.

## Controller and remaining small-signal BOM

| Exact part(s) | Package / electrical check | Evidence / remaining scope |
|---|---|---|
| RP2040 | QFN56 7×7, 0.4 mm pitch, 3.2 mm exposed ground pad; correct split 3V3 supply and internal 1V1 DVDD in source. | [Original hardware-design guide](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf), prior A1 native-board review. |
| W25Q16RVCNJQ | 16 Mbit / 2 MiB, 3 V family, CN 150 mil SOP8, Q ordering option; standard 3.9×4.9 SOIC8 maps correctly. | Exact primary-document and boot2 checks retained in [Flash review](flash-selection-review.md). Firmware needs the documented QE-mask adaptation; this is not a claim of stock UF2 hardware testing. |
| TLV75533PDBVR | 3.3 V, DBV SOT23-5; pins 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT agree. | [TI original](https://www.ti.com/lit/ds/symlink/tlv755p.pdf). 500 mA IC rating does not override board target ≤150 mA; about 0.21 W at 4.7→3.3 V and 150 mA. |
| USBLC6-2SC6 | SOT23-6; 1/6 channel1, 3/4 channel2, 2 GND, 5 rail agree. Source biases rail from VSYS. | [ST original DS4260](https://www.st.com/resource/en/datasheet/usblc6-2.pdf). Physical ESD performance depends on layout; device test is not board certification. |
| SN74LVC2G17DBVR | DBV SOT23-6; 1 A1, 2 GND, 3 A2, 4 Y2, 5 VCC, 6 Y1; 5 V-tolerant inputs with 3V3 supply. | [TI original](https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf); source pin mapping matches. |
| SN74AHCT1G125DBVR | DBV SOT23-5; 1 /OE, 2 A, 3 GND, 4 Y, 5 VCC; 4.5–5.5 V supply and TTL input threshold support 3V3 GPIO. | [TI original product/data sheet](https://www.ti.com/product/SN74AHCT1G125). Prior primary-data-sheet check established input leakage at VCC=0; no new conflicting pin evidence. |
| ABM8-272-T3 | 12 MHz, CL10 pF, max ESR50 Ω, 3225 four pad; 15 pF capacitors and 1 kΩ damping match RP2040 recommendation. | [RP2040 manufacturer's exact recommendation §2.3.1](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf). Abracon exact PDF was unavailable in this pass; package source remains earlier reference design rather than a newly read Abracon ordering sheet. |
| TL3342F160QG | Original exact part drawing exists; 5.1×5.1 body, SPST-NO, 12 V/50 mA, 160 gf, 100k cycles. Standard TL3342 footprint is appropriate family. | [E-Switch exact original drawing, linked by manufacturer](https://configured-product-images.s3.amazonaws.com/2D/specs/TL3342F160QG.pdf). Full terminal-pair orientation was not re-viewed as an image this pass; not newly certified pin-by-pin. |
| LTST-C190KGKT | Listed LED0603, source pad1 cathode ground / pad2 anode. | **Partial:** [exact original Lite-On DS22-2000-074](https://optoelectronics.liteon.com/upload/download/DS22-2000-074/LTST-C190KGKT.PDF) located, but mechanical/polarity graphics not readable this pass. Do not claim an independent exact-polarity/dimension proof merely from generic LED0603. |
| RC0603FR-0710KL, -075K1L, -07100KL, -071KL, -0749R9L, -0713K3L, -07511KL, -07105KL, -0743K2L, -07220RL | Source values correspond to suffixes 10k, 5.1k, 100k, 1k, 49.9Ω, 13.3k, 511k, 105k, 43.2k, 220Ω and 0603 footprints. | [Yageo original RC V14, 2025-11-14](https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L), pp2/4/5/7: F=1%, R paper reel, 07 standard-power 7-inch reel, R/K/M decimal notation. Exact value codes valid. 0603 body 1.60±0.10 × 0.80±0.10 mm, 1/10 W and 75 V at stated conditions; power derates above 70°C. |
| RC0402FR-0727RL, RC0402FR-071KL | Source 27Ω / 1kΩ and 0402 footprints agree with coding. | Same original Yageo RC V14: 0402 body 1.00±0.05 × 0.50±0.05 mm; 1/16 W and 50 V at stated conditions. Codes and nominal footprint agree. |
| PCB copper testpoints / NPTH mounting holes | BOM quantity zero, no purchasable semiconductor or connector. | Correctly excluded from component sourcing; no invented MPN needed. |

## Release scope

This review identifies concrete sourcing corrections and retains uncertainty honestly. It does **not** establish every small-signal exact-part drawing as newly verified, nor resolve EV3 compatibility, motor/servo currents, vendor buck simulation, physical thermal tests or fabrication acceptance. Do not relabel the whole BOM as fully primary-source certified while the partial rows remain. No restricted TI ZIP download, mirror workaround or data transfer was attempted for this audit.

## Verified replacement candidates from this audit

These candidates close the engineering selection work; their presence in the final native project and regenerated BOM must still be checked after the implementation owner applies them.

| Old part | Selected compatible candidate | Primary specification / lifecycle evidence |
|---|---|---|
| GRM32ER71E106KA12L | **GRM32DR71E106KA12L** | Murata exact D-code family linked above: 10 µF, 25 V, X7R, ±10%, 1210. Nominal land unchanged. |
| GRM155R61A105KE15D | **GRM155R61C105KA12D** | [Murata exact original print entry](https://pim.murata.com/ja-jp/pim/details/?displayChangeClass=productDetailPrint&partNum=GRM155R61C105KA12%23): 1 µF, 16 V, X5R, 0402, 1.0×0.5×0.5 mm; public original index explicitly says 生産中 (in production). D packaging listed in original family entry. |
| GRM21BR61A475KA73L | **C0805C475K4PACTU**, KEMET | [Original exact specification, generated 2026-09-09](https://yageogroup.com/download/specsheet/C0805C475K4PACTU): 4.7 µF ±10%, 16 V, X5R, 0805, 2.0±0.2 × 1.25±0.2 × 1.25±0.15 mm. [Authorized Arrow exact listing](https://www.arrow.com/en/products/c0805c475k4pactu/kemet-corporation) says Active, but zero stock / 16-week standard lead / MOQ2500 at review. Manufacturer spec is not itself an explicit lifecycle-status certificate or stock guarantee. |
| GRM1885C1H750JA01D | **C0603C750J5GACTU**, KEMET | [Original exact specification](https://yageogroup.com/download/specsheet/C0603C750J5GACTU): 75 pF ±5%, 50 V, C0G, 0603, 1.6±0.15 × 0.8±0.15 × 0.8±0.07 mm. [DigiKey exact listing](https://www.digikey.com/en/products/detail/kemet/C0603C750J5GACTU/2201170) reports Active and stock at review; this is channel lifecycle evidence, not a promise of ongoing supply. |
| MF-MSMF110-2 | **MF-MSMF110/16X-2** | Current Bourns manufacturer table explicitly lists the 16 V Style 2 part. Apply confirmed/qualified lands as discussed above. |

Rejected replacement shortcuts: `GCM1885C1H750JA16D` is also NRND; `GRM219R61A475KE34D` is also a lifecycle-risk choice. No capacitor substitution changes the fact that effective capacitance under DC bias/temperature/aging, and hence regulator stability, needs verification.

## Final implementation verification — resolved

Independent follow-up of the 2026-10-12 02:29 export confirms all five selected replacement types above are implemented in source, exact native-schematic MPN fields and grouped BOM. Counts checked: 10µF D-code ×6, 1µF 16V ×2, KEMET 4.7µF ×1, KEMET 75pF ×2, PTC /16X ×4. Thus findings 1–3 are **resolved as selection/implementation issues**, not outstanding procurement substitutions. Finding 4 (EV3) remains HOLD. Native PCB nominal values and package identities match; it does not store per-footprint MPN fields. F1 and bleeders likewise match the exact schematic/BOM identity.

Native PTC pads independently read through pcbnew are 1.5×3.2mm, centres ±2.1mm, inner gap2.7mm. F1 pads are1.0×1.8mm, centres±1.25mm. Formal ERC0 errors/0warnings; DRC0violations/0unconnected/0footprint errors; contract error list empty. Every native-file hash in release-status.json agrees with disk. This does not close the previously disclosed primary-graphic evidence limitations or manufacturing/hardware HOLDs.

Final binding: circuit.py `e90767906205461e028785313fd5f1c17ea48440ee5bd65a107c31c6d903ade2`; grouped BOM `f0c5cf2bb3d012858dbd02ae2211c91f72e71067c471840734001006346a683a`; PCB `c33afa92c1e76d124cc7d846db8a845486d428d554f05d406cef071aeb02e43b`. The earlier snapshot and its findings above are retained as the audit trail, not mislabeled as the current BOM.
