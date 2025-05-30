from rob2_evaluator.parsers import PDFDocumentParser
from typing import List, Dict, Any, Optional
from pathlib import Path


class PDFService:
    """PDF文档处理服务"""

    def __init__(self, parser: Optional[PDFDocumentParser] = None):
        self.parser = parser or PDFDocumentParser()

    def parse_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析PDF文档"""
        return self.parser.parse_document(file_path)
