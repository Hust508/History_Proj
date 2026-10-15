# 例程二：SC500CS 边缘检测 → MIPI-DSI 7 英寸屏

本工程由你提供的两个 ZIP 整合：以最终版 `lab_ex1_mipi_dsi_SC500_7inch_v2` 为硬件和显示基线，接入 `lab_ex2_edge_SC500_720P` 的 `edge_detect_96.v`。目标为 MLKPAI-F02 + MLKPAI-FC02、PH1P35MDG324、Speed -3，以及例程一所用的 HYY7BIPS27A-40 / JD9165BA、1024×600、4-lane DSI 7 英寸屏。更换屏型号时不能直接保证初始化表兼容。

默认上电功能是摄像头边缘检测，黑底白边。具体编译、时序与仿真结果见 `BUILD_REPORT.md`。没有进行实体开发板测试。

## 直接使用

1. 将完整工程解压到短路径，如 `C:/FPGA/ex2_dsi`，保留目录结构。
2. 断电，将 SC500CS 接 CSI、例程一配套的 7 英寸屏接 DSI；排线和方向沿用例程一。
3. 用 BitWriter 识别 PH1P35MDG324，通过 JTAG/SRAM 下载根目录 `DSI_EDGE_SC500_7inch_compress.bit`。
4. 等待摄像头配置、DDR 校准、面板初始化完成，观察白色轮廓。纯色场景可能大部分为黑色，可将物体移到摄像头前观察。

若需要先排除屏幕接线问题，可以下载 `diagnostics/DSI_TEST_PATTERN_from_ex1_compress.bit`。该文件逐字节来自你提供的最终版例程一，仅用于独立检查 DSI 屏幕。测试图开始有短暂黑屏，随后轮换纯色、渐变和网格。切回边缘检测镜像前重新断电上电。

## 打开和重新编译

在 TD 6.2.1 中打开：

```text
td_project/lab_ex2_edge_dsi_SC500_7inch.al
```

顶层为 `design_top_wrapper`。可以在 TD 中依次综合、布局布线、生成 bitstream，也可在工程根目录执行：

```powershell
./build.ps1 -TdHome C:/APP2/ALTD
```

脚本完成综合、布局布线、建立/保持时序检查后，才会把本次生成的镜像复制到根目录。若时序失败，请先检查 `td_project/..._Runs/phy_1/` 中的报告；不要将旧镜像误当作此次编译结果。构建会覆盖该工程目录内的同名构建结果。

## 实际数据通路

```text
SC500CS（1280×720 RAW10）
  → CSI DPHY0 RX / CSI、RAW10 解包
  → demosaic → RGB888 白平衡 AWB
  → edge_detect_96：灰度、相邻像素配对、3×3 Sobel、二值化
  → 96-bit 转 128-bit → video_in → DDR 四帧缓存
  → video_out 中心裁剪 1024×600 → mixer
  → RGB24 转 RGB32 → DSI packet / ECC / CRC
  → DPHY1 TX（4 lane）→ 7 英寸 DSI 屏
```

在写入 DDR 之前处理完整 1280×720 图像；DDR 内保存的是黑白边缘图。显示读取保持例程一的中心裁剪：原图 `x=128..1151, y=60..659`。没有缩放、旋转或拉伸。有效输出链和顶层端口不使用 HDMI。

DSI 初始化表、50 个面板命令及其延时、1024×600 时序、1344×635 总时序、4 lane、约 52.18 MHz 字节时钟、PLL、引脚、DDR 控制器、显示复位和背光控制均沿用例程一。屏幕初始化 ROM 为 `user_source/ip_source/w8_d1024_rom/config_data_panel7.mif.dat`。没有更改面板寄存器来适配边缘检测，因为边缘结果仍是 RGB888 像素。

## 阈值和算法

顶层文件 `user_source/hdl_source/design_top_wrapper.v`：

```verilog
parameter DISPLAY_TEST_PATTERN = 0,
parameter EDGE_THRESHOLD = 14'd80
```

默认阈值 80，与例程二一致。减小阈值可显示较弱边缘，也可能增加噪点；增大阈值可保留较强轮廓。修改后需要重新综合和生成镜像。`DISPLAY_TEST_PATTERN=1` 可改为 FPGA 测试图；当前根目录边缘镜像使用 `0`。

算法保留例程二的资源节省方案：每拍输入 4 个 RGB888 像素，按 `R/4 + G/2 + B/4` 求灰度，然后两两取平均；每拍计算两个 Sobel 窗口，以 `|Gx|+|Gy| >= EDGE_THRESHOLD` 二值化，每个结果复制到两个输出像素。因此完整帧尺寸保持 1280×720，但水平方向有 640 个独立检测采样点。它并非逐像素全分辨率 Sobel。

窗口采用当前行及前两行，保留原例程的因果窗口定位。前两行、每行前 4 像素输出黑色；中心裁剪不会显示这些外边界。代码使用连续视频流约定，没有停顿缓存，不应将 ready 端口当成可任意暂停的 AXI 握手接口。

## 本次修改

| 文件 | 修改内容 |
|---|---|
| `user_source/hdl_source/isp/edge_detect_96.v` | 从例程二移植灰度、双行缓存和 Sobel；补充帧标记在消隐期到达时的计数器复位，以及截断帧后的零地址重同步 |
| `user_source/hdl_source/isp/isp_top.v` | 在 AWB 与 DDR 打包之间接入边缘检测；同步传递 frame_start、valid 和 data；修正例程二 ready 重复驱动；延迟行结束状态端口 |
| `user_source/hdl_source/design_top_wrapper.v` | 增加可调阈值并传入 ISP，将连续视频链的 ready 接为常有效 |
| `.al`、两个 run 的 `.prj`、`settings.cfg` | 改为例程二工程名，加入检测源码，保留最终版例程一的 DSI、PLL、DDR、IP 与约束 |
| `verification/` | 检测结果和 DDR 打包的 RTL 仿真，以及中心裁剪地址检查；面板初始化表往返校验 |

`SOURCE_PROVENANCE.json` 记录两个输入 ZIP 校验值、改动文件、与例程一逐字节一致的文件及原测试图来源。`BUILD_MANIFEST.json` 记录交付源码和镜像的 SHA-256。

## 验证与排查

仿真不需要开发板。安装 Vivado Simulator 后可运行：

```powershell
./verification/run_sim.ps1 -VivadoBin C:/APP2/VIVADO/2025.1/Vivado/bin
python ./verification/convert_panel_init.py
python ./verification/check_project.py
```

Vivado 仅用作通用 Verilog 仿真器；实际综合、布局布线和下载目标仍是安路 TD / PH1P，工程不依赖 Xilinx DCP。

测试图也不显示时，先检查接线、排线方向、`S_mipi_tx_dpll_locked`、`S_lp_config_done`。测试图正常而边缘画面异常时，检查 `S_cam_cfg_done`、`S_init_calib_complete`、`u_isp_top.awb_valid`、`u_isp_top.edge_valid`、DDR 读写和裁剪输出。背光亮起本身不能证明视频数据正常。

实体摄像头采集、屏幕点亮、上电与热启动仍需上板确认。DSI/DPHY 的厂商加密模块没有进行完整协议动态仿真；本工程不把模块级仿真或时序通过等同于硬件验证。
