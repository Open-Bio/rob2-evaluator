from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path


class DocumentProcessor(ABC):
    """文档处理器抽象基类"""

    @abstractmethod
    def process_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理文档并返回提取的内容"""
        pass


class ContentProcessor(ABC):
    """内容处理器抽象基类"""

    @abstractmethod
    def process_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理内容并返回处理后的结果"""
        pass
