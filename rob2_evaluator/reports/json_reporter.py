import json
from typing import List, Dict, Any
from .base import BaseReporter


class JSONReporter(BaseReporter):
    """JSON报告生成器"""

    def generate(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """生成JSON报告"""

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"JSON报告已生成: {output_path}")
