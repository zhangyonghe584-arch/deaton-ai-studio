# Deaton Auto Image Case Studio

Deaton Auto 的 Windows 本地图片案例制作软件。第一版只生成图片，不包含视频导入、编辑、上传或生成。

## 工作流

1. 首页新建或打开本地案例。
2. 在单一四步工作台中放入至多六张图片：车辆外观、仪表/故障部件、分析诊断、编程流程、修复完成、标志。
3. 使用可留空、可直接输入的案例信息下拉框。
4. 需要时，勾选已有的 1–5 张案例图片后点击 OpenAI 分析；Logo 会自动一并作为视觉参考发送。结果可编辑、确认或重新分析。
5. AI 会读取本机保存的项目规则和少量历史经验，持续遵守已确认的 Logo、无编号、居中不裁切和三种差异化版式要求；图片仍由本地代码生成。
5. AI 分析为可选开关：关闭时可直接按案例信息和素材生成；开启时确认方案后，方案写入本地案例文件并由 Pillow 渲染器执行，生成五张 1080 × 1920 PNG 预览，随后另存到用户选择的文件夹。

案例默认保存在 Windows `Documents\Deaton Auto Cases`，也可通过 `DEATON_PROJECTS_DIR` 环境变量改写。案例中的 `output/` 始终保留本地成品。

## OpenAI 边界

- 仅使用 OpenAI，且必须由用户点击“分析所选素材”触发。
- 上传 1–5 张用户勾选的图片；上传前压缩至最长边 1280px、JPEG 质量 72。少于 5 张时仍正常分析，缺少阶段由方案明确处理，不虚构照片。
- 不会自动扫描素材、上传视频或调用 AI 图片/视频生成。
- API Key 可在软件左侧“API 配置”中保存到本机应用设置，也可继续使用 `OPENAI_API_KEY` 环境变量；绝不写入案例或仓库。

## 本地运行

```powershell
python -m pip install -r requirements.txt
# 可选：不在界面配置时使用环境变量
$env:OPENAI_API_KEY = "your-key"
python -m app.main
```

## Windows EXE 与桌面图标

在 Windows 开发机运行：

```powershell
.\scripts\build_windows.ps1
.\scripts\install_desktop_shortcut.ps1
```

第一个脚本输出 `dist\DeatonAutoImageStudio.exe`；第二个脚本创建 Windows 桌面快捷方式。GitHub Actions 会在 `windows-latest` 上构建 EXE 并以无 Python 应用启动器的离屏模式执行烟雾检查；发布前仍应在没有 Python 的 Windows 虚拟机或实体机上手动创建案例并生成一组图片。

## 可扩展选项

编辑 `config/options.json` 可添加下拉建议。下拉框仍允许直接输入或留空。

## 验证

```powershell
python -m unittest discover -s tests -v
```

