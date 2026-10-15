# Hust508 历史例程归档

按完成阶段保存例程一、二、三。当前触屏整合版及后续开发请前往 **[Main_Proj](https://github.com/Hust508/Main_Proj)**。

| 版本 | 独立功能 | 工程与说明 | 原始交付包 |
|---|---|---|---|
| v1.0.0 | 摄像头彩色原图 → 7 寸 DSI；保留原 7inch_v2 修订 | [例程一](versions/v1.0.0-example1/README.md) | [ZIP](downloads/lab_ex1_mipi_dsi_SC500_7inch_v2.zip) |
| v2.0.0 | Sobel 黑白边缘检测 | [例程二](versions/v2.0.0-example2/README.md) | [ZIP](downloads/lab_ex2_edge_DSI_SC500_7inch.zip) |

这些版本号是 GitHub 归档管理编号，原始工程名与修订号保留。每个目录均为可独立打开的完整交付工程；源码、IP、约束、烧写文件、验证脚本和构建报告与对应原始 ZIP 一致。

## 使用

下载整个仓库或对应 ZIP，解压到短路径；进入所选版本目录，在 TD 6.2.1 打开 `td_project/` 下的 `.al` 文件。烧写与接线步骤见各版本 README。重新构建前进入所选版本目录，再执行 `./build.ps1 -TdHome C:/APP2/ALTD`。

版本关系、日期与管理规则见 [版本索引](docs/VERSIONS.md)，原始包 SHA-256 见 [versions.json](versions.json)。历史目录保持归档内容；需要修复历史版本时通过单独分支和 PR 记录原因，不覆盖原始 ZIP。

各版本的实体上板与验证状态以对应 README / BUILD_REPORT 为准。原代码与厂商 IP 的版权及使用限制继续适用。
