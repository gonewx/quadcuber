"""装配路径回归：最终配合正确，还必须能按小步骤实际装入。"""
import unittest

import assembly_instructions as instructions
import check


class AssemblyInstructionsTests(unittest.TestCase):
    def test_guide_long_pins_are_inserted_before_the_short_side_brackets(self):
        cards,_=instructions.recipes()
        checked=0
        for card in cards:
            if card['step']!=14:
                continue
            for pin in card['new']:
                if pin.name!='6558.dat':
                    continue
                checked+=1
                self.assertLess(pin.rot[:,0] @ card['delta'],0.,'长段先进入已装好的双层侧架')
                layers=check._pin_layers(pin,[p for p in card['old'] if p.kind=='solid'])
                self.assertTrue(all(lo>=check.LPIN_COLLAR-1e-8 for _,lo,hi in layers),
                                f'{card["step"]}.{card["number"]}：挡肩不能穿过先装好的短段支架')
        self.assertEqual(checked,6)


if __name__=='__main__':
    unittest.main()
