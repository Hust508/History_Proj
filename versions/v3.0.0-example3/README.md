# 例程三 DSI 实时图像与 OSD

基于你已上板跑通的 `lab_ex1_mipi_dsi_SC500_7inch_v2`，将例程三的 Logo、字符库和六位动态帧计数接到 DSI 显示通路。默认显示 SC500CS 彩色实时画面，并叠加 OSD。

适用硬件沿用例程一：PH1P35MDG324（Speed -3）、SC500CS 摄像头、米联客 7 寸 1024×600 DSI 屏。使用 TD 6.2.1。编译及仿真结果见 `BUILD_REPORT.md`；本次新增 OSD 版本仍需实体上板确认。

## 使用步骤

1. 将整个 ZIP 解压到较短路径，例如 `C:/FPGA/ex3_osd`，保留完整目录。
2. 按已成功运行的例程一接线：摄像头接 CSI，7 寸屏接 DSI。
3. 用 BitWriter 选择 PH1P35MDG324，通过 JTAG/SRAM 下载根目录的 **`DSI_OSD_SC500_7inch_compress.bit`**。
4. 观察彩色实时图像、左上角 Logo，以及 `(375,120)` 附近黄色的“安路 CNT:”和六位计数。文字和 Logo 的空白位置透出原始画面。

图像仍从 1280×720 摄像头帧中心裁剪到 1024×600；不拉伸。计数统计的是显示帧，约每秒增加 61 次，不是秒数，也不是摄像头实际采集帧数。计数从首个显示 VSYNC 更新到 000001，999999 后回到 000000，复位清零。

KEY1 复位；KEY2 降低增益；KEY3 增加增益，保持例程一的按键逻辑。文档中的“曝光调节”应以实际代码的增益控制为准。

## 工程与数据通路

打开 `td_project/lab_ex3_osd_dsi_SC500_7inch.al`，顶层为 `design_top_wrapper`。

```text
SC500CS 1280×720 → CSI 接收及 RAW10 解包 → ISP 去马赛克和白平衡
→ DDR 四帧缓存 → video_out 中心裁剪 1024×600
→ 原 mixer 对齐像素与时序 → dsi_osd_overlay 叠加 Logo 和文字
→ RGB24 转 RGB32 → DSI 打包及 PHY → 7 寸屏
```

OSD 叠加发生在裁剪之后，因此坐标以屏幕左上角 `(0,0)` 为原点，不需要减去裁剪偏移。原 `mixer.v` 和 DDR 读取使能保持不变，避免改变例程一已验证的像素对齐关系。新增模块将 RGB、DE、HS、VS 一起经过两级寄存器，不改变每行有效像素数与帧总周期。

Logo 是例程三原始的 160×160、25 位 `{不透明标记, RGB888}` 位图。标记为 1 时替换为 Logo 像素，为 0 时保留视频。字模亮点替换为文字颜色，其他位置透出视频；Logo 不透明像素具有更高优先级。这里沿用例程三实际代码的透明键选择，不实现通用的 8 位 Alpha 混合。

例程三的大型组合 `case` 位图被逐像素转换成同步 ROM；`osd_char_lib.v` 按原文件复制。文字布局、中文及数字点阵来自例程三。显示计数以 VSYNC 上升沿触发，持续多拍的 VSYNC 每帧只计一次。

## 调整 OSD

修改 `user_source/hdl_source/design_top_wrapper.v` 开头的参数后重新编译：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `OSD_ENABLE` | 1 | 1 开启 OSD；0 输出原始图像 |
| `OSD_LOGO_X`、`OSD_LOGO_Y` | 0、0 | 160×160 Logo 左上角 |
| `OSD_TEXT_X`、`OSD_TEXT_Y` | 375、120 | 200×24 动态文字区域左上角 |
| `OSD_TEXT_COLOR` | `24'hfff200` | 黄色文字 RGB888 |
| `DISPLAY_TEST_PATTERN` | 0 | 0 摄像头；1 例程一内置测试图，也叠加 OSD |

坐标请使用非负整数。Logo 完整显示时需满足 `X≤864、Y≤440`，文字完整显示时需满足 `X≤824、Y≤576`。超出屏幕的部分不会显示。包内交付的烧写文件对应默认摄像头模式，其他参数组合需重新编译。

修改固定文字可编辑 `user_source/hdl_source/osd/dsi_osd_overlay.v` 中的 `char_code` 选择和坐标布局，字模由 `osd_char_lib.v` 提供；当前模块支持库内字符，不是任意 Unicode 文本渲染器。不要删除 `anlogic_logo.hex`，综合需要加载它。

## 重新编译与验证

在工程根目录运行：

```powershell
./build.ps1 -TdHome C:/APP2/ALTD
```

脚本执行综合、布局布线与 bitstream 生成，并检查最终建立和保持裕量。只有本次生成的镜像存在且受约束时序通过，才复制为根目录的 `DSI_OSD_SC500_7inch.bit` 与压缩版本。再次编译后的结果以本次 TD 报告为准。

也可在 TD 图形界面中顺序执行综合、布局布线和 bitstream 生成。工程、运行配置及 ROM 都使用相对路径；请保留目录结构。

RTL 仿真脚本使用本机已有的 Vivado Simulator，只用于验证 Verilog，不用于为安路芯片生成镜像：

```powershell
./verification/run_sim.ps1 -VivadoBin C:/APP2/VIVADO/2025.1/Vivado/bin
```

`verification/check_project.py` 可用 Python 3 检查工程依赖和交付文件哈希。可选 `--base-zip`、`--osd-zip` 参数用于再次对照两份原始 ZIP。`verification/osd_preview.png` 是 RTL 仿真输出，背景为合成测试像素，不是上板摄像头截图。

## 关键文件

| 文件 | 用途 |
|---|---|
| `user_source/hdl_source/design_top_wrapper.v` | 在原图像对齐与 DSI 打包之间接入 OSD，提供调整参数 |
| `user_source/hdl_source/osd/dsi_osd_overlay.v` | 屏幕坐标、六位计数、字模寻址、透明叠加及流水线 |
| `user_source/hdl_source/osd/osd_logo_rom.v` | 同步读取 Logo，使用片上存储器 |
| `user_source/hdl_source/osd/anlogic_logo.hex` | 原例程三的完整 Logo 像素 |
| `user_source/hdl_source/osd/osd_char_lib.v` | 原例程三中文、英文字母和数字点阵 |
| `build_evidence/` | 本次综合、资源、时序和仿真日志 |
| `MIGRATION_DIFF.patch` | 相对最终版例程一的代码变化 |

## 验证范围

已核对例程一的摄像头、ISP、DDR、DSI、屏幕初始化和引脚文件，除顶层插入 OSD 外，232 个原有源文件及 IP/约束文件逐字节保持一致。未接入例程二边缘检测；原始彩色图像会保留。

实际开发板的采集、排线、上电和屏幕效果仍需上板确认。DSI 打包和 PHY 使用例程一的加密 IP，未进行其内部完整动态仿真；当前 RTL 仿真覆盖新增 OSD 和裁剪地址，不等同于完整系统仿真。
