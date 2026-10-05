"""运行 Uno 诊断程序的真实解码函数；用主机模拟 GPIO，验证正交与故障统计。"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKETCH = Path(__file__).resolve().parents[1] / 'firmware/uno/ev3_encoder_test/ev3_encoder_test.ino'


@unittest.skipUnless(shutil.which('g++'), '需要 g++ 运行 Uno 解码逻辑测试')
class UnoEncoderTest(unittest.TestCase):
    def test_quadrature_and_single_phase_fault(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            (tmp / 'Arduino.h').write_text('''
#pragma once
#include <stdint.h>
#define INPUT 0
#define CHANGE 1
#define F(x) x
extern uint8_t testState;
inline int digitalRead(int pin) { return pin == 2 ? (testState >> 1) : (testState & 1); }
inline void pinMode(int, int) {}
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int, void (*)(), int) {}
inline void noInterrupts() {}
inline void interrupts() {}
inline uint32_t millis() { return 0; }
struct Console {
    void begin(int) {}
    template<class T> void print(T) {}
    template<class T> void println(T) {}
};
extern Console Serial;
''')
            (tmp / 'test.cpp').write_text('''
#include <cassert>
#include "Arduino.h"
uint8_t testState = 0;
Console Serial;
#include "''' + str(SKETCH) + '''"
void change(uint8_t state) { testState = state; onEncoderChange(); }
int main() {
    setup();
    change(1); change(3); change(2); change(0);
    assert(position == 4 && edgesA == 2 && edgesB == 2 && invalidTransitions == 0);
    change(2); change(3); change(1); change(0);
    assert(position == 0 && edgesA == 4 && edgesB == 4);
    // 只有 B 相跳变：净计数抵消，但变化次数必须保留。
    change(1); change(0);
    assert(position == 0 && edgesA == 4 && edgesB == 6);
    change(3); // 两位同时翻转，不可当成合法计数。
    assert(position == 0 && invalidTransitions == 1);
    change(3); // 重复采到同一状态，不额外计数。
    assert(invalidTransitions == 1 && edgesA == 5 && edgesB == 7);
}
''')
            result = subprocess.run(['g++', '-std=c++11', '-I', str(tmp), str(tmp / 'test.cpp'), '-o', str(tmp / 'test')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            subprocess.run([str(tmp / 'test')], check=True)
