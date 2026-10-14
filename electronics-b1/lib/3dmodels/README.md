# B1 工程内 3D 显示模型

封装统一用 `${KIPRJMOD}/lib/3dmodels/…` 引用，不需要另装 KiCad 标准 3D 库（KiCad Lite 不带）。

- 各 `*.3dshapes/`：KiCad 10 标准库模型原样副本，按 CC-BY-SA 4.0（含设计例外）分发。
- `kicad/Package_SO.3dshapes/Texas_HTSOP-8…`：DRV8871 封装模型，取自 A1 工程（同为 KiCad 标准库模型）。
- `project/`：A1 自制的简化外形模型（CC0-1.0，见 `project/LICENSE.txt`）：EV3 插座主体；SRP1245A 外包络借用来显示 12×12 功率电感。只用于外观显示，不是对应料号的精确 CAD。
