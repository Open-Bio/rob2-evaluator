from pathlib import Path
import json
from typing import List, Dict, Union, Any

from rob2_evaluator.utils.cache import cache_result, FileCache

from rob2_evaluator.services.report_service import ReportService


class ROB2Executor:
    """负责执行ROB2评估流程的类"""

    def __init__(
        self,
        document_processor=None,
        content_processor=None,
        evaluation_service=None,
        cache_dir: str = ".cache",
    ):
        if document_processor is None:
            from rob2_evaluator.processors.rob2_processor import PDFDocumentProcessor  #

            document_processor = PDFDocumentProcessor()
        if content_processor is None:
            from rob2_evaluator.processors.rob2_processor import ROB2ContentProcessor  #

            content_processor = ROB2ContentProcessor()
        if evaluation_service is None:
            from rob2_evaluator.services.evaluation_service import EvaluationService  #

            evaluation_service = EvaluationService()

        self.document_processor = document_processor
        self.content_processor = content_processor
        self.evaluation_service = evaluation_service

        # from rob2_evaluator.utils.cache import FileCache #
        self.cache = FileCache(cache_dir)

    @cache_result()
    def _process_single_file(self, input_path: Path) -> List[Dict[str, Any]]:
        """处理单个文件的核心评估流程（可缓存）"""
        print(f"Executing: Processing file {input_path.name}...")
        text_items = self.document_processor.process_document(input_path)
        relevant_items = self.content_processor.process_content(text_items)
        results = self.evaluation_service.evaluate(relevant_items)
        print(f"Executing: Finished processing file {input_path.name}.")
        return results

    def _generate_unique_key(self, base_key: str, existing_keys: Dict[str, int]) -> str:
        """基于文件基本名生成唯一键"""
        count = existing_keys.get(base_key, 0)
        existing_keys[base_key] = count + 1
        if count == 0:
            return base_key
        return f"{base_key}_{count}"

    def execute(
        self,
        inputs: Union[str, Path, List[Union[str, Path]]],
        file_extensions: List[str] | None = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        执行评估流程，支持单个文件、多个文件或文件夹输入。
        对于文件夹输入，将处理指定扩展名的文件。
        返回一个字典，键是基于文件名的唯一标识符，值是评估结果。
        """
        if file_extensions is None:
            file_extensions = [".pdf"]  # 默认处理PDF文件

        if not isinstance(inputs, list):
            inputs = [inputs]

        files_to_process: List[Path] = []
        for item_path_str in inputs:
            item_path = Path(item_path_str)
            if item_path.is_file():
                if item_path.suffix.lower() in file_extensions:
                    files_to_process.append(item_path)
                else:
                    print(
                        f"Warning: File {item_path} does not have one of the allowed extensions ({', '.join(file_extensions)}). Skipping."
                    )
            elif item_path.is_dir():
                for ext in file_extensions:
                    files_to_process.extend(list(item_path.glob(f"*{ext}")))
            else:
                print(
                    f"Warning: Input {item_path} is not a valid file or directory. Skipping."
                )

        # 去重并排序，确保处理顺序一致性（可选，但有助于调试和缓存）
        unique_files_to_process = sorted(list(set(files_to_process)))
        if not unique_files_to_process:
            print("No valid files found to process.")
            return {}

        all_results: Dict[str, List[Dict[str, Any]]] = {}
        key_counts: Dict[str, int] = {}  # 用于生成唯一键

        for file_path in unique_files_to_process:
            base_name = file_path.stem  # 文件名（不含扩展名）
            unique_key = self._generate_unique_key(base_name, key_counts)

            try:
                result = self._process_single_file(file_path)
                all_results[unique_key] = result
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                all_results[unique_key] = [
                    {"error": str(e), "file_path": str(file_path)}
                ]

        return all_results


class ROB2Reporter:
    """负责生成ROB2评估报告的类"""

    def __init__(self, report_service=None):
        if report_service is None:
            # from rob2_evaluator.services.report_service import ReportService #
            report_service = ReportService()
        self.report_service = report_service

    def generate_report(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        output_path: str = "report.html",
    ) -> None:
        """生成评估报告"""
        self.report_service.generate_report(results=results, output_path=output_path)


if __name__ == "__main__":
    executor = ROB2Executor()
    reporter = ROB2Reporter()

    print("--- Scenario 1: Single file input ---")
    single_file_path = Path("data/english/6.Besson 1998.pdf")
    results_single = executor.execute(single_file_path)
    print("\nExecution Results (Single File):")
    print(json.dumps(results_single, indent=2, ensure_ascii=False))
    reporter.generate_report(results=results_single, output_path="reports/report.json")

    print("\n--- Scenario 2: Multiple files input ---")
    folder_path = Path("data/english")
    results_multiple = executor.execute(folder_path)
    print("\nExecution Results (Multiple Files):")
    print(json.dumps(results_multiple, indent=2, ensure_ascii=False))
    reporter.generate_report(
        results=results_multiple, output_path="reports/summary.html"
    )
