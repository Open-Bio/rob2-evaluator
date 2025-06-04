import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from .base import BaseReporter


class CSVReporter(BaseReporter):
    """CSV报告生成器"""

    def generate(
        self, results: Dict[str, List[Dict[str, Any]]], output_path: str
    ) -> None:
        """生成CSV报告

        Args:
            results: 评估结果数据，格式为 {文件标识: [结果列表]}
            output_path: 输出文件路径
        """
        study_results = []

        # 处理每个研究的结果
        for study_id, study_data in results.items():
            study_result = {"Study": study_id}

            for entry in study_data:
                domain = entry["domain"]
                if domain == "Overall risk of bias":
                    study_result["Overall"] = entry["judgement"]["overall"]
                else:
                    study_result[domain] = entry["overall"]["risk"]

            study_results.append(study_result)

        # 创建数据框并保存
        df = pd.DataFrame(study_results)
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"CSV报告已生成: {output_path}")
