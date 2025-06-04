from pathlib import Path
import json
from typing import List, Dict, Any

from rob2_evaluator.utils.cache import cache_result


class ROB2Evaluator:
    """ROB2评估器主类"""

    def __init__(
        self,
        document_processor=None,
        content_processor=None,
        evaluation_service=None,
        cache_dir: str = ".cache",
    ):
        # 如果没有提供依赖，则使用默认实现（保持向后兼容）
        if document_processor is None:
            from rob2_evaluator.processors.rob2_processor import PDFDocumentProcessor

            document_processor = PDFDocumentProcessor()
        if content_processor is None:
            from rob2_evaluator.processors.rob2_processor import ROB2ContentProcessor

            content_processor = ROB2ContentProcessor()
        if evaluation_service is None:
            from rob2_evaluator.services.evaluation_service import EvaluationService

            evaluation_service = EvaluationService()

        # 所有依赖在构造时就确定，不再有懒加载
        self.document_processor = document_processor
        self.content_processor = content_processor
        self.evaluation_service = evaluation_service

        # 其他服务保持不变
        from rob2_evaluator.services.report_service import ReportService
        from rob2_evaluator.utils.cache import FileCache

        self.report_service = ReportService()
        self.cache = FileCache(cache_dir)

    @cache_result()
    def process_file(self, input_path: Path) -> List[Dict[str, Any]]:
        """处理单个文件的完整评估流程"""
        # 文档处理
        text_items = self.document_processor.process_document(input_path)

        # 内容处理
        relevant_items = self.content_processor.process_content(text_items)

        # 执行评估 - 不再需要检查是否为None
        return self.evaluation_service.evaluate(relevant_items)

    def generate_report(
        self,
        results: List[Dict[str, Any]],
        output_path: str = "report.html",
    ) -> None:
        """生成评估报告"""
        self.report_service.generate_report(results=results, output_path=output_path)


if __name__ == "__main__":
    evaluator = ROB2Evaluator()
    results = evaluator.process_file(Path("examples/2.Angelone.pdf"))
    print(json.dumps(results, indent=4, ensure_ascii=False))
    # 生成评估报告
    evaluator.generate_report(results, output_path="output.docx")
