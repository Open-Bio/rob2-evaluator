from rob2_evaluator.processors.base_processor import DocumentProcessor, ContentProcessor
from rob2_evaluator.services.pdf_service import PDFService
from rob2_evaluator.agents.entry_agent import EntryAgent
from typing import List, Dict, Any, Optional
from pathlib import Path


class PDFDocumentProcessor(DocumentProcessor):
    """PDF文档处理器实现"""

    def __init__(self, pdf_service: Optional[PDFService] = None):
        self.pdf_service = pdf_service or PDFService()

    def process_document(self, file_path: Path) -> List[Dict[str, Any]]:
        return self.pdf_service.parse_document(file_path)


class ROB2ContentProcessor(ContentProcessor):
    """ROB2内容处理器实现"""

    def __init__(self, entry_agent: Optional[EntryAgent] = None):
        self.entry_agent = entry_agent or EntryAgent()

    def process_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理并过滤内容"""
        return self.entry_agent.filter_relevant(content)
