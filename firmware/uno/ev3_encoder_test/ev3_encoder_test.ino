/* EV3 编码器交叉测试：Uno + Bricktronics Motor Driver。
 * 接线：Uno 5V -> 板 VCC，GND -> GND，选中端口 T1 -> D2，T2 -> D3。
 * 两个端口的 EN 接 GND，DIR/PWM 接 GND；VM 不接电源。
 * 只手动转轴，不输出任何马达控制信号，不启用输入上拉。
 * 串口 115200；每秒报告两相边沿、非法状态跳变、位置增量与累计位置。
 * 换马达、线缆或端口前拔 USB，换好再上电，计数自动重置。
 * 详见 docs/ev3-uno-crosscheck.md。
 */
#include <Arduino.h>

const uint8_t PIN_A = 2;
const uint8_t PIN_B = 3;
volatile uint8_t previousState = 0;
volatile uint32_t edgesA = 0;
volatile uint32_t edgesB = 0;
volatile uint32_t invalidTransitions = 0;
volatile int32_t position = 0;

// 00 -> 01 -> 11 -> 10 -> 00 记为正；实际物理方向不作规定。
const int8_t STEP[16] = {
    0, 1, -1, 0,
    -1, 0, 0, 1,
    1, 0, 0, -1,
    0, -1, 1, 0
};

uint8_t readState() {
    return (digitalRead(PIN_A) << 1) | digitalRead(PIN_B);
}

void onEncoderChange() {
    const uint8_t state = readState();
    const uint8_t changed = state ^ previousState;
    if (changed & 2) ++edgesA;
    if (changed & 1) ++edgesB;
    if (changed == 3) {
        ++invalidTransitions;
    } else {
        position += STEP[(previousState << 2) | state];
    }
    previousState = state;
}

void setup() {
    pinMode(PIN_A, INPUT);
    pinMode(PIN_B, INPUT);
    Serial.begin(115200);
    previousState = readState();
    attachInterrupt(digitalPinToInterrupt(PIN_A), onEncoderChange, CHANGE);
    attachInterrupt(digitalPinToInterrupt(PIN_B), onEncoderChange, CHANGE);
    Serial.println(F("EV3 encoder test: VM disconnected, EN grounded. Turn shaft by hand."));
    Serial.println(F("A/B/bad/delta: per interval; pos: cumulative; state: sampled AB."));
}

void loop() {
    static uint32_t lastReport = 0;
    static int32_t lastPosition = 0;
    const uint32_t now = millis();
    if (now - lastReport < 1000) return;
    lastReport = now;

    // Uno 是 8 位 MCU，读取/清零共享的多字节计数时暂时关闭中断。
    noInterrupts();
    const uint32_t a = edgesA, b = edgesB, bad = invalidTransitions;
    const int32_t pos = position;
    const uint8_t state = readState();
    edgesA = edgesB = invalidTransitions = 0;
    interrupts();

    Serial.print(F("A=")); Serial.print(a);
    Serial.print(F(" B=")); Serial.print(b);
    Serial.print(F(" bad=")); Serial.print(bad);
    Serial.print(F(" delta=")); Serial.print(pos - lastPosition);
    Serial.print(F(" pos=")); Serial.print(pos);
    Serial.print(F(" state=")); Serial.print(state >> 1); Serial.println(state & 1);
    lastPosition = pos;
}
