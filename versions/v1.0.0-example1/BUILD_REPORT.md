# v2 构建报告

交付日期：2026-10-12（Asia/Shanghai）。TD V6.2.168116 / PH1P35MDG324 / Speed -3。

摄像头版和独立测试图版均实际完成综合、布局布线、bitstream 生成，最终 Slow/Fast 两种 corner 的受检查路径无时序违例。

| 镜像 | 建立 SWNS (ns) | 保持 HWNS (ns) | STA coverage |
|---|---:|---:|---:|
| camera | 0.115 | 0.020 | 95.79% |
| test_pattern | 0.034 | 0.020 | 95.70% |

STA coverage 不等于 100%；结论适用于当前约束覆盖的路径，不等于上板验证。工程延续厂商异步时钟分组，新增显示复位同步释放，未为隐藏违例而豁免整条正常显示链。

## 本次补充资料带来的修正

- 使用 `MLK_MIPI屏7寸/01_hardware/hardware.rar` 中的真实 `7inch_init_sequence.coe`，50 个 DSI 包和参数按原序转换；Sleep Out 后 120 ms、Display On 后 32 ms。原安路 ROM 的部分面板参数不同，且最后含 NOP / 不同延时，不继续作为有效初始化。
- 安路随板参考提供 DSI packetizer、LP 和 PH1P DPHY TX；屏幕包提供的 Xilinx DCP 不兼容 PH1P，没有放入安路工程。
- DPLL 配置 15/1，TD 最终报告确认约 52.18 MHz 字节时钟；1344×635 总时序调度约 61.14 Hz，接近新屏手册的约 52 MHz / 60 Hz 方案。不是严格 60.000 Hz，也不是旧版约 80 Hz。
- 10 ms 初始化前等待、初始化后 200 ms 背光等待；保留参考的 LP/PHY 逻辑。底板 40-pin 组件图中的 FFC 33 是触摸 TP-RES，因此保持释放，未把它当 LCD RESX。
- 保留 720P 摄像头、CSI、ISP、DDR 相关 108 个源码文件，逐字节匹配输入 HDMI ZIP；显示端中心裁剪至 1024×600。

## 已执行验证

- 两种模式的综合、布局布线、受约束建立/保持时序检查及压缩/非压缩 bitstream 生成。
- TD 从工程目录打开 `.al` 成功并分析源文件，日志无 ERROR。
- 独立解析器检查 COE → ROM → DSI 包的往返转换，实际 DAT 与原始 COE 的所有命令、参数和延时完全一致；综合日志确认读取该 DAT。
- 相对工程文件路径存在性检查；前半段源码 SHA-256 比对。
- 中心裁剪采用此前版本的相同 RTL：此前数值模型覆盖四个帧地址、460800 个 DDR 字地址及 2457600 个 RGB888 像素。此模型不是 RTL 动态仿真；此前仿真器未正常完成，不宣称 RTL 仿真通过。

## 尚未验证

没有连接实体开发板进行采集、屏幕点亮、排线、电源轨或热启动测试。加密 DSI 协议/PHY 未作完整动态仿真。芯片的裸面板 RESET/内部电源轨到 40-pin 组件的完整电路未提供；按配套参考及组件接口工作，不编造控制引脚。请先用测试图镜像验证 DSI，再用摄像头镜像上板。

各镜像、源文件和 ROM 的 SHA-256 见 `BUILD_MANIFEST.json`；详细日志、资源和时序报告见 `build_evidence/`。
默认 `.al` 源码参数为 0，对应 camera；测试图编译参数为 1，其唯一不同的顶层源码保存在 `verification/test_pattern_design_top_wrapper.v`，重建用 `build_test_pattern.ps1`。
