from pathlib import Path
from typing import Dict, Any, List, Optional
from rob2_evaluator.factories.reporter_factory import ReporterFactory
from rob2_evaluator.config.report_config import ReportConfig


class ReportService:
    """报告生成服务"""

    def __init__(
        self,
        reporter_factory: Optional[ReporterFactory] = None,
        default_config: Optional[ReportConfig] = None,
    ):
        """
        初始化报告服务

        Args:
            reporter_factory: 报告生成器工厂，支持依赖注入
            default_config: 默认报告配置
        """
        self.reporter_factory = reporter_factory or ReporterFactory()
        self.default_config = default_config or ReportConfig()

    def generate_report(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        output_path: str,
        config: Optional[ReportConfig] = None,
    ) -> None:
        """
        生成评估报告

        Args:
            results: 评估结果数据，格式为 {文件标识: [结果列表]}
            output_path: 输出文件路径
            config: 报告配置（可选，使用默认配置如果未提供）
        """
        effective_config = config or self.default_config

        # 文件扩展名决定报告类型，移除前置的点号
        report_type = Path(output_path).suffix.lstrip(".").lower()

        reporter = self.reporter_factory.create(
            report_type=report_type, config=effective_config
        )
        reporter.generate(results, output_path)
