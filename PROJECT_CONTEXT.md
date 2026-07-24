# Deaton Auto AI Studio 项目说明

## 项目目标

这是 Deaton Auto 的 Windows 本地汽车远程编程案例图片制作软件。用户只需放入案例照片、填写案例信息，软件负责分析素材、规划版式并在本地生成五张案例成品图。

当前阶段只完善图片制作功能，不扩展视频功能，也不改变已经确定的四步工作台结构。

## 用户工作方式

1. 打开或新建一个本地案例。
2. 放入最多六张图片：车辆外观、仪表或故障部件、分析诊断、编程过程、修复完成、Logo。
3. 填写案例信息；所有字段可以留空，也允许直接输入。
4. 可选择 1–5 张案例图片，手动调用 OpenAI 分析。
5. 用户确认或修改 AI 方案后，由本地渲染器生成五张成品图。
6. 用户检查预览并保存到自己选择的文件夹。

AI 分析是可选功能。关闭 AI 时，软件仍可根据案例信息和本地素材直接生成图片。

## 已确定的产品边界

- 软件在 Windows 本地运行。
- 只制作图片，不添加视频导入、视频剪辑或视频生成。
- 不增加复杂首页、案例展示页、素材排序、批量管理和自动扫描。
- OpenAI 只在用户点击分析按钮后调用。
- 原始图片、项目数据和成品默认保存在本地。
- 图片渲染继续由本地 Pillow 代码完成，不使用 AI 重新绘制车辆照片或 Logo。
- API Key 只保存在用户电脑的应用设置或环境变量中，不能写入仓库、案例或项目说明。

## 固定生成规则

- 每个案例生成五张 1080 × 1920 PNG 图片。
- 即使素材不足五张，也要合理安排五张成品，但不能虚构不存在的车辆、故障或维修照片。
- 同一案例至少包含三种有明显差异的版式方向，避免五张图完全套用同一个模板。
- 原始照片居中完整显示，不能随意裁掉车辆、仪表和故障细节。
- Logo 区域只显示 Logo。
- 不添加 STEP、步骤编号、图片编号、案例编号或无意义占位数字。
- 生成前允许用户编辑和确认 AI 分析方案。

## 品牌规则

- 当前项目使用用户提供或案例 Logo 槽中的品牌图。
- 新案例默认使用仓库中的品牌资源，但用户可在同一 Logo 槽替换。
- Logo 必须保持原始结构和比例，不能由 AI 重画、变形或擅自添加文字。
- 用户此前要求后续案例优先使用 YH 标志，不再使用旧标志；如果仓库中的默认品牌资源尚未替换，必须先向用户确认，不能自行改动。

## 现有技术结构

- 主程序：Python Windows 桌面应用。
- 本地案例：`core.case_store.CaseStore` 管理 `case.json`、六个固定图片槽和 `output/`。
- AI 方案：`core.ai_plan.OpenAIPlanService`。
- 本地项目记忆：`core.ai_memory.ProjectMemory`。
- 图片渲染：`core.local_renderer`。
- 生成服务：`core.generation.LocalGenerationService`。
- 下拉选项：`config/options.json`。
- 默认案例目录：Windows `Documents\\Deaton Auto Cases`。
- 可通过 `DEATON_PROJECTS_DIR` 修改案例保存目录。

## 验证与交付

本地开发验证命令：

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m app.main
```

Windows 打包命令：

```powershell
.\scripts\build_windows.ps1
.\scripts\install_desktop_shortcut.ps1
```

打包结果为 `dist\DeatonAutoImageStudio.exe`。发布前需要在 Windows 上实际创建案例、生成五张图片并检查排版、文字、Logo 和保存流程。

## 后续协作规则

- 开始修改前先阅读 `AGENTS.md`、本文件和 `README.md`。
- 先检查现有实现和 Git 状态，不重复已完成的工作。
- 不随意改变目录结构、按钮、四步流程和已确认的生成规则。
- 一次只处理用户明确要求的范围。
- 修改后运行相关测试并明确说明改了什么、没有改什么。
- 未经用户明确要求，不提交、不推送、不发布，也不删除已有文件。
