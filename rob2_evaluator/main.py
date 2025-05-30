from pathlib import Path
import json
from typing import List, Dict, Any

from rob2_evaluator.services.evaluation_service import EvaluationService
from rob2_evaluator.services.report_service import ReportService
from rob2_evaluator.processors.rob2_processor import (
    PDFDocumentProcessor,
    ROB2ContentProcessor,
)
from rob2_evaluator.utils.cache import FileCache, cache_result


class ROB2Evaluator:
    """ROB2评估器主类"""

    def __init__(self, cache_dir: str = ".cache"):
        self.document_processor = PDFDocumentProcessor()
        self.content_processor = ROB2ContentProcessor()
        self.evaluation_service = None
        self.report_service = ReportService()
        self.cache = FileCache(cache_dir)

    @cache_result()
    def process_file(self, input_path: Path) -> List[Dict[str, Any]]:
        """处理单个文件的完整评估流程"""
        # 文档处理
        text_items = self.document_processor.process_document(input_path)

        # 内容处理
        relevant_items = self.content_processor.process_content(text_items)

        # 执行评估
        if not self.evaluation_service:
            self.evaluation_service = EvaluationService()

        return self.evaluation_service.evaluate(relevant_items)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        output_path: str = "report.html",
    ) -> None:
        """
        生成评估报告

        Args:
            results: 评估结果数据
            output_path: 输出文件路径，系统将根据文件扩展名自动确定报告类型
        """
        self.report_service.generate_report(results=results, output_path=output_path)


if __name__ == "__main__":
    evaluator = ROB2Evaluator()
    results = evaluator.process_file(Path("examples/2.Angelone.pdf"))
    print(json.dumps(results, indent=4, ensure_ascii=False))
    # 生成评估报告
    evaluator.generate_report(results)
