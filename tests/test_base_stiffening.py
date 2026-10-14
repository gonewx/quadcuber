"""Final lower-frame geometry contract; no physical stiffness certification."""
import collections
import json
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'mechanical'))
import candidate as c

class BaseStiffening(unittest.TestCase):
    def test_final_inventory_and_unchanged_head_support(self):
        self.assertEqual(len(c.retained_base()),120)
        self.assertEqual(len(c.full_machine({})),946)
        self.assertEqual(len(c.core_parts()),150)
        self.assertEqual(len(c.state_parts({})),676)
        counts=collections.Counter(p.name for p in c.retained_base())
        old=collections.Counter(p.name for p in c.retained_base_r4())
        self.assertEqual(dict(counts-old),{'32278.dat':8,'32526.dat':4,'40490.dat':8,'6558.dat':40,'32523.dat':4})
        self.assertEqual(dict(old-counts),{'2780.dat':8})

    def test_from_scratch_recipe_matches_final_instances(self):
        book=json.loads((Path(__file__).resolve().parents[1]/'mechanical/assembly/base-steps.json').read_text())
        seen=set();added=[]
        for step in book['steps']:
            added+=step['added_part_ids'];seen.update(step['added_part_ids'])
            self.assertLessEqual(set(step['visible_part_ids']),seen,step['id'])
            for row in step['geometry_records']:
                p=c.retained_base()[row['index1']-1]
                self.assertEqual(row['name'],p.name)
                np.testing.assert_allclose(row['position_ldu'],p.pos)
                np.testing.assert_allclose(row['rotation'],p.rot)
        self.assertEqual(collections.Counter(added),collections.Counter(range(1,121)))
        self.assertEqual(len(book['steps']),77)

    def test_upper_corner_instructions_use_new_shoulder_plane(self):
        book=json.loads((Path(__file__).resolve().parents[1]/'mechanical/assembly/base-steps.json').read_text())
        for step in book['steps']:
            if set(step['added_part_ids']) & {23,39,55,60}:
                text=' '.join(step['instructions'])
                self.assertIn('肩圈在Y116',text,step['id'])
                self.assertNotIn('中央挡圈留在L梁与下梁之间',text)
                self.assertNotIn('Y108毫米接缝',text)

    def test_connection_validator_rejects_reversed_actual_pin(self):
        import runpy
        from unittest.mock import patch
        import base_stiffening
        original=base_stiffening.reinforce
        def reverse_pin(*args):
            final,new,connections=original(*args)
            pin=next(p for p in new if p.name=='6558.dat')
            pin.rot=pin.rot@np.diag([-1,-1,1])
            return final,new,connections
        with patch.object(base_stiffening,'reinforce',reverse_pin):
            with self.assertRaisesRegex(AssertionError,'OUT-2-120'):
                runpy.run_path(str(Path(__file__).resolve().parents[1]/'mechanical/assembly/check_base_stiffening.py'))

    def test_foot_contact_plane_and_no_forbidden_thin_beams(self):
        pp=c.retained_base()
        self.assertAlmostEqual(max(c.world(p)[...,1].max() for p in pp),140)
        feet=[p for p in pp if p.note.startswith('FOOT-')]
        self.assertEqual(len(feet),4)
        self.assertEqual({tuple(np.round(p.pos*.4,6)) for p in feet},{(152.,136.,-32.),(32.,136.,152.),(-152.,136.,32.),(-32.,136.,-152.)})
        self.assertFalse({'32017.dat','32063.dat'}&{p.name for p in pp})

if __name__=='__main__':unittest.main()
