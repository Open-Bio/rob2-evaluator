from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseReporter(ABC):
    """报告生成器基类"""

    @abstractmethod
    def generate(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """生成报告"""
        pass
