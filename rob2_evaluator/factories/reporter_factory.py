from typing import Optional
from rob2_evaluator.reports.base import BaseReporter
from rob2_evaluator.reports.csv_reporter import CSVReporter
from rob2_evaluator.reports.html_reporter import HTMLReporter
from rob2_evaluator.reports.json_reporter import JSONReporter
from rob2_evaluator.reports.word_reporter import WordReporter
from rob2_evaluator.config.report_config import ReportConfig


class ReporterFactory:
    """报告生成器工厂类"""

    def __init__(self):
        self._reporters = {
            "csv": CSVReporter,
            "html": HTMLReporter,
            "json": JSONReporter,
            "docx": WordReporter,
        }

    def create(
        self, report_type: str, config: Optional[ReportConfig] = None
    ) -> BaseReporter:
        """
        创建报告生成器实例

        Args:
            report_type: 报告类型（如 'csv', 'html', 'json', 'docx'）
            config: 报告配置（可选）

        Returns:
            BaseReporter: 报告生成器实例

        Raises:
            ValueError: 如果指定的报告类型不支持
        """
        reporter_class = self._reporters.get(report_type.lower())
        if reporter_class is None:
            supported = ", ".join(self._reporters.keys())
            raise ValueError(
                f"不支持的报告类型: {report_type}。支持的类型: {supported}"
            )

        return reporter_class()
