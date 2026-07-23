import os
import sys
from pathlib import Path

RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
PROJECTS_DIR = Path(os.getenv("DEATON_PROJECTS_DIR", Path.home() / "Documents" / "Deaton Auto Cases"))
DEFAULT_LOGO = RESOURCE_DIR / "resources" / "branding" / "deaton_auto_logo.png"

SLOT_SPECS = (
    ("vehicle", "车辆外观"),
    ("fault", "仪表 / 故障部件"),
    ("diagnosis", "分析诊断"),
    ("programming", "编程流程"),
    ("result", "修复完成"),
    ("logo", "标志"),
)

CASE_FIELDS = (
    ("brand", "车辆品牌"),
    ("model", "车型"),
    ("year", "年份"),
    ("fault_category", "故障"),
    ("service", "服务"),
    ("programming", "编程"),
    ("result", "结果"),
)

DEFAULT_OPTIONS = {
    "brand": ["BMW / 宝马", "Mercedes-Benz / 奔驰", "Porsche / 保时捷", "Audi / 奥迪", "Volkswagen / 大众", "Toyota / 丰田"],
    "model": [""],
    "year": [str(year) for year in range(2026, 1989, -1)],
    "fault_category": ["ECU", "BCM", "Immobilizer", "Key", "Dashboard", "No Start"],
    "service": ["Remote Programming", "Remote Diagnostics", "OEM Coding", "Module Replacement"],
    "programming": ["ECU Programming", "Module Coding", "Key Programming", "Calibration"],
    "result": ["Programming Completed", "Function Restored", "Vehicle Started", "Fault Cleared"],
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
