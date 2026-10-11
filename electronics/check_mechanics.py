#!/usr/bin/env python3
"""Reproduce the PCB underside clearance review; does not modify mechanics.

This is a sampled mesh-envelope check, not continuous collision certification.
Run from any directory with the mechanical project's numpy dependency installed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mechanical"))
import candidate as model


def bounds(parts):
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for part in parts:
        xyz = model.world(part).reshape(-1, 3)
        lo = np.minimum(lo, xyz.min(axis=0))
        hi = np.maximum(hi, xyz.max(axis=0))
    return {"min_mm": lo.tolist(), "max_mm": hi.tolist()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angle-step", type=int, default=5)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "generated/electronics/mechanical-review.json")
    args = parser.parse_args()
    if args.angle_step < 1 or 360 % args.angle_step:
        parser.error("angle-step must be a positive divisor of 360")
    # All four arm transforms preserve Y exactly. One local arm consequently
    # proves the same sampled Y envelope for each of the four mounted arms.
    arm_rotations = {}
    for name, rotation in model.m.ARM_ROT.items():
        rotation = np.asarray(rotation)
        if not np.allclose(rotation[1], [0, 1, 0]):
            raise AssertionError("Arm transform no longer preserves Y: " + name)
        arm_rotations[name] = rotation.tolist()
    samples = []
    for angle in range(0, 360, args.angle_step):
        for opening in [0.0, float(model.m.OPEN_S)]:
            envelope = bounds(model.module(opening, angle, on_base=True))
            samples.append({"angle_deg": angle,
                            "opening_stroke_mm": opening * 0.4,
                            "max_y_mm": envelope["max_mm"][1]})
    support = [{"drop_mm": drop,
                "bounds": bounds(model.core_parts(drop, locks=False))}
               for drop in [0.0, 20.4, 40.8]]
    base = bounds(model.retained_base())
    max_y = max(base["max_mm"][1],
                max(row["max_y_mm"] for row in samples),
                max(row["bounds"]["max_mm"][1] for row in support))
    source_files = [ROOT / "mechanical/candidate.py",
                    ROOT / "mechanical/inputs/baseline_model.py",
                    ROOT / "mechanical/inputs/baseline-machine-899.mpd",
                    ROOT / "mechanical/inputs/assembly132.json",
                    ROOT / "mechanical/inputs/assembly-integrated-R1.json"]
    source_files += sorted((ROOT / "mechanical/parts").glob("*.dat"))
    report = {
        "method": "sampled transformed LDraw triangle envelopes; 1 LDU = 0.4 mm; positive Y downward",
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_files},
        "angle_step_deg": args.angle_step,
        "arm_rotation_y_invariance_verified": True,
        "arm_rotations": arm_rotations,
        "arm_samples": samples,
        "support_samples": support,
        "base_bounds": base,
        "sampled_max_y_mm": max_y,
        "proposed_pcb_solder_face_y_mm": 124.0,
        "sampled_mesh_clearance_mm": 124.0 - max_y,
        "pcb_dimensions_mm": [144, 112],
        "pcb_hole_spacing_mm": [136, 104],
        "pcb_orientation": "solder face up; components downward; X/Z centered on robot",
        "physical_validation": False,
        "manufacturing_release": False,
        "limitations": [
            "Finite angle and support-position samples, not continuous sweep proof.",
            "Jaw opening sampled only at closed/open endpoints.",
            "Bracket, legs, screws, cable sweep, manufacturing tolerances and board height are not modeled.",
            "8 mm is bare-model separation; protruding solder leads reduce that space.",
            "Existing Technic holes are not certified mating PCB mounting points.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{len(samples)} arm samples; max Y {max_y:.3f} mm; "
          f"bare-mesh gap {124.0-max_y:.3f} mm; NOT physical clearance approval")


if __name__ == "__main__":
    main()
