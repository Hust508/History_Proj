# 例程一：SC500CS → MIPI-DSI 7 英寸屏（v2）

适用开发板：提供的 MLKPAI-F02 + MLKPAI-FC02，PH1P35MDG324，Speed -3。
适用显示屏：此前确认的套装 HYY7BIPS27A-40 / 米联客 7 英寸、1024×600、JD9165BA 模组。
这是基于原 SC500 HDMI 720P 例程修改的完整 TD 6.2.1 工程。
源文件的摄像头模式、CSI RX、ISP、DDR 写入和 DDR 控制器保持原样。

## 先这样使用

1. 将整个 ZIP 解压到短路径，例如 `C:/FPGA/dsi7`。不要单独取出 `.al` 文件；TD 对过长路径支持不完整。
2. 断电连接 SC500CS 到 **CSI**，显示屏到 **DSI**，使用厂商配套同向 40-pin 屏幕排线，注意 MLK/LCM 端方向。
3. 用 BitWriter 识别 **PH1P35MDG324**，先以 JTAG/SRAM 下载 `DSI_TEST_PATTERN_compress.bit`。
4. 下载后观察约 3 秒：测试图从黑色切换到纯色、渐变和网格，每约 2 秒换一种。初始短暂黑屏是测试图模式 0，不能据此判断失败。
5. 测试图正常后，重新上电并下载 **`DSI_SC500_7inch_v2_compress.bit`**，显示摄像头中心区域。

测试图直接来自 FPGA，显示内容不依赖摄像头和 DDR 像素返回。摄像头镜像才用于完成例程一。
两类镜像使用相同的 DSI lane、显示时序、初始化表和背光控制。
本包的编译与时序结论见 `BUILD_REPORT.md`；没有实际连接开发板验证点亮。

## 打开与重新编译

打开 `td_project/lab_ex1_mipi_dsi_SC500_7inch_v2.al`，顶层为 `design_top_wrapper`。
在 TD 中依次综合、布局布线、生成 bitstream；或在工程目录运行：

```powershell
./build.ps1 -TdHome C:/APP2/ALTD
```

独立重建测试图而保留摄像头工程源码：

```powershell
./build_test_pattern.ps1 -TdHome C:/APP2/ALTD -WorkDir C:/FPGA/dsi7_pattern
```

WorkDir 必须是新的可写短目录。脚本不删除旧工程。测试图等价于顶层参数 `DISPLAY_TEST_PATTERN=1`；默认 `0` 为摄像头图像。
再次编译后，以本次 TD 日志及时序报告为准，随包校验值对应交付时构建。

## 数据链

```text
SC500CS 1280×720 → CSI DPHY0 RX → CSI/RAW10 解包 → ISP
→ video_in → DDR 四帧缓存 → video_out 中心裁剪 1024×600
→ mixer → RGB24 转 RGB32 → DSI video packet / ECC / CRC
→ PH1P DPHY1 TX（4 lane）→ DSI 40-pin 屏幕
```

原 `video_out` 是按读请求输出 RGB888，并不自己生成 DE/VS/HS。本工程用厂商 `video_source` 产生屏幕时序，`mixer` 对齐 DDR 像素及 DE/VS/HS，再接 DSI 打包链。
HDMI VTC、TX、PHY 和 TMDS 端口已从有效输出链移除。

原画面中 `x=128..1151, y=60..659` 显示在屏幕上；每个输出像素对应原图一个像素，不缩放、旋转或拉伸。
DDR 中仍保存完整 1280×720。每行读取 192 个 128-bit 字，保留原 1280 像素行跨度。
开始新帧时排空上一帧已提交的读取，再复位像素 FIFO。

## 显示参数

| 项目 | v2 配置 |
|---|---|
| 有效区域 / 总时序 | 1024×600 / 1344×635 |
| 水平 HSA/HBP/HFP | 24 / 136 / 160 |
| 垂直 VSA/VBP/VFP | 2 / 21 / 12 |
| 格式 / 模式 | RGB888；Video Non-Burst with Sync Events |
| 物理层 | DPHY1，4 data lanes，BYTE_NUM=1，连续 clock lane |
| 系统输入 | 板载 C4 的 25 MHz |
| PLL 输出 | 100 MHz DDR 参考、24 MHz 摄像头、52.173913 MHz DPLL 参考、10 MHz LP 控制 |
| DPLL 配置值 | MULTI_RATIO=15，DIV_RATIO=1 |
| 视频调度 / 字节时钟 | TD 最终时序报告约 52.18 MHz，约 61.14 帧/秒 |
| lane 速率 / HS clock | 约 417.4 Mbps / 208.7 MHz，按字节时钟换算 |
| LP 时钟 | 控制器输入 10 MHz；这不表示 LP 线速就是 10 Mbps |
| D-PHY 时序计数 | 沿用安路参考：DATA 10/10/20/10；CLK 10/10/10/10/10/10 |

时序计数的单位由厂商 IP 决定，不能直接当作纳秒。
保持安路随板参考的 porch 和 PHY 实现；新版将旧约 80 Hz 调度降至接近屏幕手册所用的 52 MHz / 60 Hz。
61.14 Hz 是实际时钟及固定总时序的计算值，不宣称严格为 60.000 Hz。
裸面板规格书第 13 页列出典型总时序 1344×635、典型 DCLK 51.2 MHz；新屏幕手册使用约 52 MHz。

## 初始化、供电和背光

初始化直接使用这次屏幕硬件包的 **`7inch_init_sequence.coe`**。
把其 50 个 DSI 包原样转换成安路 LP 控制器 ROM 指令，未修改寄存器值。
包含 `Sleep Out (11h)` 后 **120 ms**、`Display On (29h)` 后 **32 ms** 等待。
实际生效文件是 `user_source/ip_source/w8_d1024_rom/config_data_panel7.mif.dat`；旧 `config_data_nes` 只作为原参考留下，不被本工程 ROM 引用。
`PANEL_INIT_COMMANDS.json` 给出逐包内容；`verification/convert_panel_init.py` 检查 COE 与实际 DAT 的命令、参数和延时完全一致。

DPLL 锁定后先等待 10 ms，再执行 LP 初始化。这个裕量是实现选择，不是屏幕规格书要求的精确数值。
背光在初始化完成后再等 200 ms 打开，覆盖 JD9165BA 上电图中的十个 VSYNC 等待。
新显示复位分别在 DDR、DSI 和 LP 时钟域同步释放。

板上 3.3 V 由硬件常供电，没有 FPGA panel power-enable GPIO。
**底板 T10 / FFC 33 在屏幕组件图中是 TP-RES（触摸复位），不是裸面板 RESET/芯片 RESX。**
沿用端口名 `O_screen_reset_n` 保持其高电平释放，不把它冒充 LCD 硬复位。
裸面板内部供电/RESET 到组件板的完整电路未给出，不能实现或宣称验证了这些内部电源轨。
建议首次测试和切换镜像均重新上电；本工程不保证在屏幕已处于 Sleep Out 时直接重新配置 FPGA 的热启动行为。
触摸功能不在本次改动范围内。

## 接线及约束

核心板固定 DPHY1 pad 对应底板 DSI FFC；普通 LVCMOS ADC 不用于指定专用 PHY 的差分 lane。

| 信号 | FPGA P/N | 底板 FFC P/N |
|---|---|---|
| CLK | N18 / P17 | 23 / 24 |
| D0 | R18 / T17 | 27 / 26 |
| D1 | P18 / R17 | 21 / 22 |
| D2 | M18 / N17 | 19 / 18 |
| D3 | L18 / M17 | 14 / 13 |

P/N 和 lane 顺序未交换。背光 R11 → FFC 29；TP-RES T10 → FFC 33。
FFC 1/2 为组件 3.3 V。裸面板规格书中的 31-pin 接口不同于该组件的 40-pin 接口，不能直接照搬。
ADC 使用提供的板卡摄像头 T9/U9/V9/V8、背光 R11、TP-RES T10。
SDC 约束 25 MHz 输入并由 TD 派生 DSI 时钟；对异步时钟组及新增同步器的复位置位作针对性约束。

## 修改文件

| 文件/目录 | 用途 |
|---|---|
| `design_top_wrapper.v` | 替换 HDMI 输出链，接 DSI、初始化、背光和测试图选择 |
| `video_out.v` | 从 720P 帧缓存中心裁剪到 1024×600 |
| `display_reset_sync.v` | 新显示链跨时钟复位同步释放 |
| `video_source.v`、`video_tpg.v`、`mixer.v` | 厂商显示时序、测试图和像素对齐 |
| `dsi_tx_packet/`、`mipi_dphy_tx/` | 厂商 DSI 控制/打包、LP 和 PH1P D-PHY TX |
| `w8_d1024_rom/` | 新屏初始化原始 COE 及转换 ROM |
| `PLL/`、`pin.adc`、工程 `.sdc` | 实际板载时钟、引脚及时序约束 |

`UNCHANGED_FRONTEND_SHA256.json` 校验 108 个摄像头/CSI/ISP/DDR 文件与用户的原 HDMI ZIP 逐字节相同。
厂商加密 IP 原样使用，需要 TD 6.2.1；Xilinx DCP 不能用于安路芯片，未将其作为工程依赖。

## 黑屏时如何定位

- 测试图也没有：先检查下载识别、排线方向、25 MHz PLL、`S_mipi_tx_dpll_locked`、`S_lp_config_done`。背光亮不等于 DSI 数据正常。
- 测试图正常、摄像头版不正常：检查 `S_cam_cfg_done`、CSI/RAW10 valid、ISP valid、`S_init_calib_complete` 和 DDR 读写。
- 摄像头画面只有中心部分：这是本工程的中心裁剪行为。

未接板验证屏幕初始化、实际采集和点亮；完整 DSI 加密逻辑也未做动态仿真。请以首次上板结果完成最终确认。
