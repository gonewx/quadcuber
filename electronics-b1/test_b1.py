"""B1 引脚映射回归：不依赖 KiCad，直接解析原生 PCB 和导出网表。映射错一个脚整块板就废了，DRC 查不出来。"""
import re
import runpy
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARMS = runpy.run_path(str(ROOT / 'wiring/spec.py'))['ARMS']
# 官方 Pico pinout（从顶面看 USB 朝上，左列 1..20 自上而下，右列 21..40 自下而上）。
PICO = {1: 'GP0', 2: 'GP1', 4: 'GP2', 5: 'GP3', 6: 'GP4', 7: 'GP5', 9: 'GP6', 10: 'GP7', 11: 'GP8', 12: 'GP9',
        14: 'GP10', 15: 'GP11', 16: 'GP12', 17: 'GP13', 19: 'GP14', 20: 'GP15', 21: 'GP16', 22: 'GP17',
        24: 'GP18', 25: 'GP19', 26: 'GP20', 27: 'GP21', 39: 'VSYS'}
PICO_GND = {3, 8, 13, 18, 23, 28, 33, 38}


def pcb_pads():
    """{(位号, 焊盘号): 网络名}，直接读 .kicad_pcb 文本。"""
    text = (HERE / 'quadcuber-b1.kicad_pcb').read_text()
    pads = {}
    for fp in re.split(r'\n\t\(footprint ', text)[1:]:
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
        for num, body in re.findall(r'\(pad "([^"]*)" (.*?)\n\t\t\)', fp, re.S):
            net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', body)
            if num:
                pads.setdefault((ref, num), net.group(1) if net else None)
    return pads


class B1Pinmap(unittest.TestCase):
    def setUp(self):
        self.pads = pcb_pads()

    def test_pico_pins_follow_official_pinout(self):
        for pin, net in PICO.items():
            self.assertEqual(self.pads[('U3', str(pin))], net, pin)
        for pin in PICO_GND:
            self.assertEqual(self.pads[('U3', str(pin))], 'GND', pin)
        for pin in (36, 40):  # 3V3 输出、VBUS 不接外部电源
            self.assertTrue((self.pads[('U3', str(pin))] or '').startswith('unconnected-'), pin)

    def test_pico_table_matches_breadboard_wiring(self):
        """第二来源：wiring/build.py 中已在面包板实测接线用过的 Pico 引脚表。"""
        import ast
        import runpy
        table = {}
        for node in ast.parse((ROOT / 'wiring/build.py').read_text()).body:
            if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in ('PICO_LEFT', 'PICO_RIGHT'):
                table.update(ast.literal_eval(node.value))
        ours = runpy.run_path(str(HERE / 'circuit.py'))['PICO_PINS']
        alias = {'AGND': 'GND', 'ADC_VREF': 'VREF'}
        self.assertEqual(len(table), 40)
        self.assertEqual({k: alias.get(v, v) for k, v in ours.items()}, table)

    def test_each_arm_matches_wiring_spec(self):
        for i, (arm, (motor, enc, servo, _sm)) in enumerate(ARMS.items()):
            n = 10 * (i + 1)
            drv, ev3 = f'U{n}', f'J{n+1}'
            self.assertEqual(self.pads[(drv, '3')], f'GP{motor[0]}')   # IN1
            self.assertEqual(self.pads[(drv, '2')], f'GP{motor[1]}')   # IN2
            self.assertEqual(self.pads[(drv, '5')], 'VM')
            for pad in ('1', '7', '9'):
                self.assertEqual(self.pads[(drv, pad)], 'GND')
            self.assertEqual([self.pads[(ev3, str(k))] for k in range(1, 7)],
                             [f'{arm}_M1', f'{arm}_M2', 'GND', '5V_LOGIC', f'{arm}_ENC_A_RAW', f'{arm}_ENC_B_RAW'])
            self.assertEqual(self.pads[(drv, '6')], f'{arm}_M1')
            self.assertEqual(self.pads[(drv, '8')], f'{arm}_M2')
            # 编码器：原始信号经 10k 到 GPIO，GPIO 经 20k 到地
            self.assertEqual({self.pads[(f'R{n+1}', '1')], self.pads[(f'R{n+1}', '2')]}, {f'{arm}_ENC_A_RAW', f'GP{enc[0]}'})
            self.assertEqual({self.pads[(f'R{n+2}', '1')], self.pads[(f'R{n+2}', '2')]}, {f'GP{enc[0]}', 'GND'})
            self.assertEqual({self.pads[(f'R{n+3}', '1')], self.pads[(f'R{n+3}', '2')]}, {f'{arm}_ENC_B_RAW', f'GP{enc[1]}'})
            self.assertEqual({self.pads[(f'R{n+4}', '1')], self.pads[(f'R{n+4}', '2')]}, {f'GP{enc[1]}', 'GND'})
            self.assertEqual([self.pads[(f'J{n}', k)] for k in '123'], ['GND', 'SERVO_5V', f'{arm}_SERVO'])
            self.assertEqual({self.pads[(f'R{n+5}', '1')], self.pads[(f'R{n+5}', '2')]}, {f'GP{servo[0]}', f'{arm}_SERVO'})

    def test_power_path(self):
        p = self.pads
        self.assertEqual([p[('Q1', k)] for k in '123'], ['GATE', 'VIN_F', 'VM'])        # G D S
        self.assertEqual([p[('DZ1', k)] for k in '12'], ['VM', 'GATE'])                 # 阴极接源极
        self.assertEqual([p[('U1', k)] for k in '12345'], ['VM', 'BUCK_SW', 'GND', 'SERVO_5V', 'GND'])
        self.assertEqual([p[('U2', k)] for k in '123'], ['VM', 'GND', '5V_LOGIC'])
        self.assertEqual([p[('D3', k)] for k in '12'], ['VSYS', '5V_LOGIC'])
        self.assertEqual([p[('D1', k)] for k in '12'], ['VM', 'GND'])

    def test_netlist_matches_pcb(self):
        path = ROOT / 'generated/electronics-b1/netlist.xml'
        if not path.exists():
            self.skipTest('netlist not built')
        for net in ET.parse(path).getroot().iter('net'):
            for node in net.iter('node'):
                self.assertEqual(self.pads[(node.get('ref'), node.get('pin'))], net.get('name'))


if __name__ == '__main__':
    unittest.main()
