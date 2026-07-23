import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal

RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
PROJECTS_DIR = Path(os.getenv("DEATON_PROJECTS_DIR", Path.home() / "Documents" / "Deaton Auto Cases"))
DEFAULT_LOGO = RESOURCE_DIR / "resources" / "branding" / "deaton_auto_logo.png"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

SLOT_SPECS = (
    ("vehicle", "车辆外观 / Vehicle Exterior"),
    ("fault", "仪表与故障部件 / Dashboard & Fault"),
    ("diagnosis", "分析诊断 / Diagnosis"),
    ("programming", "编程流程 / Programming"),
    ("result", "修复完成 / Repair Completed"),
    ("logo", "标志 / Logo"),
)

CASE_FIELDS = (
    ("brand", "车辆品牌 / Vehicle Brand"),
    ("model", "车型 / Vehicle Model"),
    ("year", "年份 / Model Year"),
    ("region", "车辆地区 / Vehicle Region"),
    ("fault_category", "故障类别 / Fault Category"),
    ("service", "服务类型 / Service Type"),
    ("programming", "编程项目 / Programming Task"),
    ("result", "处理结果 / Repair Result"),
)

DEFAULT_OPTIONS = {
    "brand": ["BMW / 宝马", "Mercedes-Benz / 奔驰", "Porsche / 保时捷", "Audi / 奥迪", "Volkswagen / 大众", "Toyota / 丰田"],
    "model": [""],
    "year": [str(year) for year in range(2026, 1989, -1)],
    "region": ["United States / 美国", "Canada / 加拿大", "United Kingdom / 英国", "Germany / 德国", "Australia / 澳大利亚", "Hong Kong / 中国香港", "Macau / 中国澳门", "Mainland China / 中国大陆", "Other / 其他"],
    "fault_category": ["ECU / 发动机电脑", "BCM / 车身控制模块", "Immobilizer / 防盗系统", "Key / 钥匙系统", "Dashboard / 仪表系统", "No Start / 无法启动", "Communication / 通讯故障", "Coding Error / 编码错误", "Other / 其他"],
    "service": ["Remote Programming / 远程编程", "Remote Diagnostics / 远程诊断", "OEM Coding / 原厂编码", "Module Replacement / 模块更换", "Key Programming / 钥匙编程", "ADAS Calibration / ADAS校准", "Technical Support / 技术支持"],
    "programming": ["ECU Programming / ECU编程", "Module Coding / 模块编码", "Software Flashing / 软件刷写", "Key Programming / 钥匙编程", "Configuration / 配置设定", "Calibration / 校准"],
    "result": ["Programming Completed / 编程完成", "Function Restored / 功能恢复", "Vehicle Started / 车辆成功启动", "Fault Cleared / 故障排除", "Repair Completed / 修理完成", "Pending Further Test / 待进一步测试"],
}
