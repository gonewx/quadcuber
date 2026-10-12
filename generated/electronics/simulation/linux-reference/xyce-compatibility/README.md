# Xyce 7.10 / original TI TPS54302 dialect probes

Prepared from local official Xyce 7.10 source and original TI library. **These netlists have not yet been run.** No TI library, transistor/device parameters, or repository files were changed. Synthetic RC component values are test fixtures only.

Run after Xyce is built:

```sh
python /workspace/tool-verification/xyce-compatibility/run_units.py /absolute/path/to/Xyce --hspice-negative-control
```

Each attempt has a separate runs/<mode>/<test>/stdout.log and CSV, and runs/results.json records actual return codes. Successful process exit is not sufficient: inspect numerical outputs and warnings, especially ignored .IC nodes.

## Mathematical expectations

* `xor_exact.cir`: exact expression from TI line 664, `V(YTD) > 0.5 ^ V(IN) > .5`. `xor_parenthesized.cir`: explicit grouping of those comparisons. `xor_adapted.cir`: parenthesized Boolean comparisons with `!=`. All three must match `xor_expected.csv` in default mode. Equality to 0.5 is false. Sweep covers all nine combinations of 0, 0.5, 1 V. The optional HSPICE-math run is a deliberate negative control: XOR netlists should fail semantic comparison while adapted != remains valid. Do not enable math/all for the full original TI model.
* `logic_value.cir`: AS=AD=Boolean AND, OS=OD=Boolean OR, GS=GE=-1 V for A<=0.5 V and +2 V above 0.5 V. Covers single/double logical spellings, IF, nested braces, E VALUE, G VALUE and optional `=`. Source-current direction is tested by G flowing from ground into a 1 kohm resistor.
* `switch_transfer.cir`: unchanged `_U8_S31` model parameters (TI line 372). At control<=0.4 V R=10 Mohm; >=1.1 V R=0.04 ohm; midpoint 0.75 V R=sqrt(0.04*1e7)=632.455532 ohm. With 1 V across switch, I(VTEST)=-1/R. All 19 values are in `switch_expected.csv`. This distinguishes continuous transition from abrupt/hysteretic SW substitutions.
* `ic_alias_space.cir` / `ic_alias_compact.cir`: formal EN and COMP map to ACTUAL_EN and ACTUAL_COMP; original whitespace in `V(EN )` must be harmless. UIC initial values EN=0 and COMP=1.3695 V (nonzero STEADY_STATE test fixture chosen to make ignored IC detectable). With tau=1 ms, EN(t)=1-exp(-t/tau), COMP(t)=1.3695*exp(-t/tau). Actual first output time may exceed zero.
* `ic_no_equals.cir` / `ic_with_equals.cir`: isolate TI latch `.IC V(Qint) {VSS}` (594,632,653,692) versus equals-only repair. VSS=0.25 is a test fixture to detect ignored IC; expected OUT(t)=0.25*exp(-t/1ms). Default VSS=0 would hide a silently ignored IC.
* `rc_op_noic.cir`: normal operating point gives OUT=1 V. `rc_uic_noic.cir` and `rc_noop_noic.cir`: skip OP, OUT(t)=1-exp(-t/1ms). All three `_ic` variants use `.IC V(OUT)=0.25` and should start at 0.25 V with OUT(t)=1-0.75*exp(-t/1ms). UIC and NOOP must agree. Compare at actual times; an absent t=0 row is not a failure.

A reasonable check is <=1e-8 absolute for digital outputs, 1e-5 relative for DC switch values, and 0.2% absolute full-scale for these transient RC tests with 1 us maximum step. Record actual deviations instead of adjusting model parameters to meet expectations.

## Exact source evidence

All source paths below are relative to `/workspace/tools/src/xyce-7.10/src/`.

* `UtilityPKG/ExpressionSrc/ExpressionLexer.l:264-269`: `|` and `||` share TOK_OR, `&` and `&&` share TOK_AND; caret is TOK_CARET.
* `UtilityPKG/ExpressionSrc/ExpressionParser.yxx:725-736`: comparisons have higher precedence than caret; caret higher than AND/OR. AND and OR share precedence, so do not assume C precedence for mixed chains. TI XOR phrase therefore groups each comparison as intended.
* `UtilityPKG/ExpressionSrc/ExpressionParser.yxx:1783-1792`: caret creates powOp if useHspiceMath, xorOp otherwise. `IOInterfacePKG/N_IO_ParsingMgr.C:104-115`: math and all enable that flag.
* `UtilityPKG/ExpressionSrc/astcomp.h:182-191`: comparisons produce Boolean 0/1; xorOp applies positive versus nonpositive truth. With comparison operands, it exactly agrees with !=. Do not generalize this adaptation to arbitrary analog operands.
* `UtilityPKG/ExpressionSrc/ExpressionParser.yxx:1741-1743` and `ast.h:4253-4277`: IF chooses true branch for nonzero real condition; only selected branch evaluated in val(). TI conditions are comparisons, avoiding ambiguity with negative condition values.
* `IOInterfacePKG/N_IO_DeviceBlock.C:835-859,876-899`: E/G VALUE recognized and converted internally to B sources; optional equals accepted. This is native implementation, not a reason to rewrite the user model.
* `DeviceModelPKG/OpenModels/N_DEV_SW.C:672-673`: VSWITCH recognized; :508,520-538 and :949-994 implement continuous log-cubic transition. :754-755 define Lm=log(sqrt(RON*ROFF)), Lr=log(RON/ROFF). For normalized u=(control-VOFF)/(VON-VOFF), s=2u-1, log(R)=Lm+0.75*Lr*s-0.25*Lr*s^3 inside transition.
* `IOInterfacePKG/N_IO_InitialConditions.C:591-607`: parser selects V(node)=value syntax only when equals exists; :711-750 no-equals mode instead parses node/value token pairs. Original `.IC V(Qint) {VSS}` is therefore a concrete suspected syntax incompatibility, pending runtime confirmation.
* `IOInterfacePKG/N_IO_InitialConditions.C:295-307`: subcircuit interface alias X1:A maps to actual node; :310-315 writes requested initial value. Whitespace and mapping still need runtime test.
* `AnalysisPKG/N_ANP_Transient.C:246-249`: UIC and NOOP both setNOOP(true); :879 derives dcopFlag from it; :924-925 says IC/NODESET can be used in both modes; :976 and :999 note no t=0 PRN output under UIC/NOOP.

## Minimal compatibility strategy

1. Attempt the full original TI reference unchanged, default Xyce dialect, before any adaptation. Preserve diagnostics.
2. Run these probes and verify numeric outputs. Do not apply the prior ngspice XOR patch: native Xyce already implements the original meaning.
3. If runtime proves the missing-equals IC syntax unsupported, make a separate auditable copy with only four `.IC V(Qint) {VSS}` lines converted to `.IC V(Qint)={VSS}`. This preserves exactly the intended initial values and all physical/device parameters. Do not remove the IC lines, move aliases blindly, change N/IS/C/R values, smooth hard comparators, or replace continuous VSWITCH by a threshold switch.
4. Syntax correctness does not establish convergence or physical validation. The full original/reference-equivalent result must pass before the real BOM nine-case sweep.

PSpice behavior is represented by the original TI model's declared PSpice dialect and requested mathematical semantics; this task has not run PSpice as an independent oracle. Parent also verified the official Xyce 7.10 Reference Guide, p164 (^ Boolean XOR; ** power), p762-765 (continuous VSWITCH), p843 (behavioral-source compatibility). Do not label unit agreement as full-model validation.
