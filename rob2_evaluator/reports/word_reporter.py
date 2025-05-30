from typing import List, Dict, Any
from pathlib import Path
from docx import Document
from docx.shared import Inches
from .base import BaseReporter


class WordReporter(BaseReporter):
    """Word报告生成器"""

    def generate(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """生成Word格式的报告

        Args:
            results: 评估结果列表
            output_path: 输出文件路径
        """
        # 创建一个新的Word文档
        doc = Document()
        study_id = Path(output_path).stem

        # 添加标题
        doc.add_heading(f"ROB2评估报告 - {study_id}", 0)

        # 添加总体评估结果表格
        doc.add_heading("总体评估结果", level=1)
        overall_table = doc.add_table(rows=1, cols=2)
        overall_table.style = "Table Grid"
        header_cells = overall_table.rows[0].cells
        header_cells[0].text = "评估领域"
        header_cells[1].text = "风险评估"

        for entry in results:
            domain = entry["domain"]
            row_cells = overall_table.add_row().cells
            row_cells[0].text = domain
            if domain == "Overall risk of bias":
                row_cells[1].text = entry["judgement"]["overall"]
            else:
                row_cells[1].text = entry["overall"]["risk"]

        # 添加详细信号评估
        doc.add_heading("详细评估结果", level=1)
        detailed_table = doc.add_table(rows=1, cols=6)
        detailed_table.style = "Table Grid"

        # 设置表头
        header_cells = detailed_table.rows[0].cells
        headers = [
            "Domain",
            "Signal",
            "Answer",
            "Reason",
            "Evidence (text)",
            "Evidence (pages)",
        ]
        for i, header in enumerate(headers):
            header_cells[i].text = header

        # 添加详细评估数据
        for entry in results:
            domain_name = entry.get("domain", "")
            signals = entry.get("signals", {})

            if not isinstance(signals, dict):
                continue

            for signal_key, signal_data in signals.items():
                row_cells = detailed_table.add_row().cells
                row_cells[0].text = domain_name
                row_cells[1].text = signal_key
                row_cells[2].text = signal_data.get("answer", "")
                row_cells[3].text = signal_data.get("reason", "")

                # 处理evidence
                evidence = signal_data.get("evidence", [])
                evidence_texts = " | ".join([e["text"] for e in evidence])
                evidence_pages = ", ".join(str(e["page_idx"]) for e in evidence)

                row_cells[4].text = evidence_texts
                row_cells[5].text = evidence_pages

        # 保存文档
        output_path_docx = str(Path(output_path).with_suffix(".docx"))
        doc.save(output_path_docx)
        print(f"Word报告已生成: {output_path_docx}")
