import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseReporter


class CSVReporter(BaseReporter):
    """CSV报告生成器"""

    def generate(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """生成CSV报告

        Args:
            results: 评估结果列表
            output_path: 输出文件路径
        """
        # 使用Path处理文件路径
        study_id = Path(output_path).stem

        study_result = {"Study": study_id}

        for entry in results:
            domain = entry["domain"]
            if domain == "Overall risk of bias":
                study_result["Overall"] = entry["judgement"]["overall"]
            else:
                study_result[domain] = entry["overall"]["risk"]

        df = pd.DataFrame([study_result])
        df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"CSV报告已生成: {output_path}")
