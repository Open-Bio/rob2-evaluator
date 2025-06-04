import json
from typing import Dict, Any, List
from .base import BaseReporter


class JSONReporter(BaseReporter):
    """JSON报告生成器"""

    def generate(
        self, results: Dict[str, List[Dict[str, Any]]], output_path: str
    ) -> None:
        """生成JSON报告

        Args:
            results: 评估结果数据，格式为 {文件标识: [结果列表]}
            output_path: 输出文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"JSON报告已生成: {output_path}")
