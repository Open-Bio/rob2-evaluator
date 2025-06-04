from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import List, Dict, Any, Union
from .base import BaseReporter


class HTMLReporter(BaseReporter):
    """HTML报告生成器"""

    def __init__(
        self, template_path: str | Path = "templates/report_template_summary.html.j2"
    ):
        """
        初始化HTML报告生成器

        Args:
            template_path: 模板文件路径，相对于项目根目录
        """
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        full_template_path = project_root / template_path
        template_dir = full_template_path.parent

        if not template_dir.exists():
            raise ValueError(f"Template directory not found: {template_dir}")

        self.template_name = full_template_path.name
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)), autoescape=True
        )

    def generate(
        self,
        file_results: Dict[str, List[Dict[str, Any]]],
        output_path: Union[str, Path],
    ) -> None:
        """
        生成HTML报告

        Args:
            file_results: 文件结果字典，格式为 {文件标识: [结果列表]}
            output_path: 输出文件路径
        """
        from rob2_evaluator.schema.rob2_schema import DOMAIN_SCHEMAS

        DOMAIN_HEADER_MAPPING = {
            "randomization": "Randomization",
            "deviation_assignment": "Deviations (Assignment)",
            "deviation_adherence": "Deviations (Adherence)",
            "missing_data": "Missing Data",
            "measurement": "Measurement",
            "selection": "Selection",
        }
        template = self.env.get_template(self.template_name)
        html = template.render(
            file_results=file_results,
            domain_schemas=DOMAIN_SCHEMAS,
            domain_header_mapping=DOMAIN_HEADER_MAPPING,
        )

        output = Path(output_path)
        output.write_text(html, encoding="utf-8")

        print(f"HTML报告已生成: {output}")
        print(f"共处理 {len(file_results)} 个文件")
