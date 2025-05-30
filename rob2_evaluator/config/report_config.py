from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HTMLReportConfig:
    """HTML报告配置"""

    template_path: Path = Path("templates") / "report_template.html.j2"


@dataclass
class JSONReportConfig:
    """JSON报告配置"""

    include_timestamp: bool = True
    include_summary: bool = True


@dataclass
class ReportConfig:
    """报告配置容器"""

    html: HTMLReportConfig = field(default_factory=HTMLReportConfig)
    json: JSONReportConfig = field(default_factory=JSONReportConfig)
