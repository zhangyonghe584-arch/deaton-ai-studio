import os
import sys
from pathlib import Path

RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
PROJECTS_DIR = Path(os.getenv("DEATON_PROJECTS_DIR", Path.home() / "Documents" / "Deaton Auto Cases"))
DEFAULT_LOGO = RESOURCE_DIR / "resources" / "branding" / "deaton_auto_logo.png"

SLOT_SPECS = (
    ("vehicle", "车辆外观"),
    ("fault", "仪表 / 故障部件"),
    ("diagnosis", "诊断过程"),
    ("programming", "编程过程"),
    ("result", "修复完成"),
    ("logo", "官方 Logo"),
)

CASE_FIELDS = (
    # 只保留适合公开展示的已完成案例事实；过程状态和内部沟通不进入案例。
    ("brand", "车辆品牌"),
    ("model", "车型"),
    ("year", "年份"),
    ("mileage", "里程"),
    ("location", "车辆地区"),
    ("customer_issue", "客户问题"),
    ("fault_category", "故障类别"),
    ("dtc_codes", "故障码或故障现象"),
    ("diagnosis", "诊断发现"),
    ("service", "完成的服务项目"),
    ("programming", "完成的编程处理"),
    ("programming_detail", "处理内容"),
    ("result", "修复结果"),
    ("final_status", "案例结论"),
    ("equipment", "使用设备"),
    ("verification", "修复验证"),
)

DEFAULT_OPTIONS = {
    "brand": ["BMW / 宝马", "Mercedes-Benz / 奔驰", "Porsche / 保时捷", "Audi / 奥迪", "Volkswagen / 大众", "Toyota / 丰田"],
    "model": [""],
    "year": [str(year) for year in range(2026, 1989, -1)],
    "mileage": [],
    "location": [],
    "customer_issue": [],
    "fault_category": ["ECU / 发动机控制单元", "BCM / 车身控制模块", "ADAS / 高级驾驶辅助", "Immobilizer / 防盗系统", "Key / 钥匙系统", "Dashboard / 仪表系统", "Gateway / 网关模块", "Airbag / 安全气囊", "No Start / 无法启动", "Communication / 通讯故障"],
    "service": ["Remote Diagnostics / 远程诊断", "Remote Programming / 远程编程", "OEM Coding / 原厂编码", "Module Replacement / 模块更换", "Component Protection / 组件保护处理", "ECU Adaptation / ECU 匹配学习", "Fault Memory Clearing / 故障码清除"],
    "programming": ["ECU Programming / ECU 编程", "Module Coding / 模块编码", "Parameterization / 参数化", "Component Protection / 组件保护", "Key Programming / 钥匙编程", "Adaptation & Learning / 匹配与学习", "Calibration / 校准", "Software Update / 软件升级"],
    "programming_detail": [],
    "result": ["Programming Completed / 编程完成", "Function Restored / 功能恢复", "Vehicle Started / 车辆启动", "Fault Cleared / 故障清除", "System Activated / 系统激活", "Adaptation Completed / 匹配完成", "No Critical Faults / 无严重故障"],
    "final_status": [],
    "dtc_codes": [],
    "equipment": [],
    "verification": [],
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

