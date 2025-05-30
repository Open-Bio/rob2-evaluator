import json
from typing import List, Dict, Any
from .base import BaseReporter


class JSONReporter(BaseReporter):
    """JSON报告生成器"""

    def generate(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """生成JSON报告"""
        report_data = {
            "timestamp": self._get_timestamp(),
            "results": results,
            "summary": self._generate_summary(results),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"JSON报告已生成: {output_path}")

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成结果摘要"""
        if not results:
            return {"total": 0}

        return {
            "total": len(results),
            "domains": list(
                set(r.get("domain", "") for r in results if r.get("domain"))
            ),
        }
