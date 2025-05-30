from rob2_evaluator.reports import (
    BaseReporter,
    HTMLReporter,
    JSONReporter,
    CSVReporter,
    WordReporter,
)
from rob2_evaluator.config.report_config import (
    ReportConfig,
    HTMLReportConfig,
    JSONReportConfig,
)


class ReporterFactory:
    """报告生成器工厂类"""

    @staticmethod
    def create_html_reporter(config: HTMLReportConfig | None = None) -> HTMLReporter:
        """
        创建HTML报告生成器

        Args:
            config: HTML报告配置

        Returns:
            HTMLReporter: HTML报告生成器实例
        """
        if config is None:
            config = HTMLReportConfig()

        return HTMLReporter(template_path=config.template_path)

    @staticmethod
    def create_json_reporter(config: JSONReportConfig | None = None) -> JSONReporter:
        """
        创建JSON报告生成器

        Args:
            config: JSON报告配置

        Returns:
            JSONReporter: JSON报告生成器实例
        """
        if config is None:
            config = JSONReportConfig()

        return JSONReporter()

    @staticmethod
    def create_csv_reporter() -> CSVReporter:
        """
        创建CSV报告生成器

        Returns:
            CSVReporter: CSV报告生成器实例
        """
        return CSVReporter()

    @staticmethod
    def create_word_reporter() -> WordReporter:
        """
        创建Word报告生成器

        Returns:
            WordReporter: Word报告生成器实例
        """
        return WordReporter()

    @staticmethod
    def create(report_type: str, config: ReportConfig | None = None) -> BaseReporter:
        """
        根据类型创建报告生成器

        Args:
            report_type: 报告类型 ("html" 或 "json")
            config: 报告配置

        Returns:
            BaseReporter: 对应的报告生成器实例

        Raises:
            ValueError: 不支持的报告类型
        """
        if config is None:
            config = ReportConfig()

        report_type = report_type.lower()

        if report_type == "html":
            return ReporterFactory.create_html_reporter(config.html)
        elif report_type == "json":
            return ReporterFactory.create_json_reporter(config.json)
        elif report_type == "csv":
            return ReporterFactory.create_csv_reporter()
        elif report_type in ["docx", "doc"]:
            return ReporterFactory.create_word_reporter()
        else:
            raise ValueError(f"不支持的报告类型: {report_type}")
