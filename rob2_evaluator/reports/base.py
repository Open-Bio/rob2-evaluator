from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseReporter(ABC):
    """报告生成器基类"""

    @abstractmethod
    def generate(
        self, results: Dict[str, List[Dict[str, Any]]], output_path: str
    ) -> None:
        """
        生成报告

        Args:
            results: 评估结果数据，格式为 {文件标识: [结果列表]}
            output_path: 输出文件路径
        """
        pass
