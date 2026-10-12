# Quadcuber A1 MicroPython启动适配

Flash为W25Q16RVCNJQ。QUADCUBER_A1继承Pico硬件配置，唯一启动行为变化是只检查QE位，兼容RV-Q默认SR2=06h。完整依据见[Flash复核](../sources/flash-selection-review.md)。不修改应用GPIO、PIO或控制协议；USB UF2流程不变。原库软件仍只验证R/L逐臂。

## 重建

依赖Git、CMake、Make、GCC Arm Embedded/Newlib及Python3。Debian可安装cmake、gcc-arm-none-eabi、libnewlib-arm-none-eabi、libstdc++-arm-none-eabi-newlib、build-essential、pkg-config；工具只从发行版仓库或上游官方来源取得。

```sh
git clone --branch v1.27.0 --depth 1 https://github.com/micropython/micropython.git /tmp/quadcuber-micropython
git -C /tmp/quadcuber-micropython submodule update --init --depth 1 lib/pico-sdk lib/tinyusb lib/mbedtls lib/micropython-lib
make -C /tmp/quadcuber-micropython/mpy-cross -j4
make -C /tmp/quadcuber-micropython/ports/rp2 BOARD=QUADCUBER_A1 BOARD_DIR=/absolute/path/to/quadcuber/electronics/firmware/QUADCUBER_A1 -j4
python /absolute/path/to/quadcuber/electronics/firmware/verify_build.py /tmp/quadcuber-micropython/ports/rp2/build-QUADCUBER_A1
```

输出在MicroPython的`ports/rp2/build-QUADCUBER_A1/firmware.uf2`。构建使用固定子模块，不替换为任意最新SDK。若CMake提示picotool缺失，它会从Raspberry Pi官方仓库构建。提供的boot2保留上游BSD-3-Clause许可证。

本次构建的UF2和`firmware-check.json`放在`generated/electronics/firmware/`，仅供首板验证，未烧录或通电。不要将旧官方RPI_PICO UF2与此适配版混淆。硬件未放行状态不变。

本次使用GCC Arm 14.2.1、CMake 3.31.6，完整UF2构建成功。验证1318个UF2块、RP2040 family ID、Flash地址范围、240字节boot2和ROM CRC；反汇编确认QE检测跳转到状态写之后。此验证不模拟QSPI电气时序或证明实机启动。
