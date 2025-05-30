from jinja2 import Environment, FileSystemLoader
import os
from typing import Dict, Any, List, Optional


class ReportService:
    """报告生成服务"""

    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            template_dir = os.path.dirname(os.path.dirname(__file__))
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def generate_report(
        self, results: List[Dict[str, Any]], template_name: str, output_path: str
    ) -> None:
        """生成评估报告"""
        from rob2_evaluator.schema.rob2_schema import DOMAIN_SCHEMAS

        template = self.env.get_template(template_name)
        html = template.render(results=results, domain_schemas=DOMAIN_SCHEMAS)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"评估报告已生成: {output_path}")
