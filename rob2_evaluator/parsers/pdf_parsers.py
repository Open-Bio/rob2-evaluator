from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker  # type: ignore
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
import logging


class PDFDocumentParser:
    """PDF文档解析器，用于提取和过滤PDF文档内容"""

    def __init__(self, excluded_headings: Optional[Set[str]] = None):
        """
        初始化PDF解析器

        Args:
            excluded_headings: 需要过滤的标题集合，默认过滤 "references"
        """
        self.converter = DocumentConverter()
        self.chunker = HybridChunker()
        self.excluded_headings = excluded_headings or {"references"}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def parse_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        解析PDF文档并返回过滤后的文本块

        Args:
            file_path: PDF文件路径

        Returns:
            包含文本和页码信息的字典列表

        Raises:
            FileNotFoundError: 当文件不存在时
            Exception: 解析过程中的其他错误
        """
        try:
            self.logger.info(f"开始解析文档: {file_path}")

            # 验证文件存在
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 转换文档
            conv_res = self.converter.convert(file_path)
            doc = conv_res.document

            # 分块处理
            chunk_iter = self.chunker.chunk(doc)
            chunk_list = list(chunk_iter)

            self.logger.info(f"文档分割为 {len(chunk_list)} 个块")

            # 过滤块
            filtered_chunks = self._filter_chunks(chunk_list)
            self.logger.info(f"过滤后剩余 {len(filtered_chunks)} 个块")

            # 提取文本和页码
            text_items = self._extract_text_items(filtered_chunks)

            self.logger.info(f"成功解析文档，提取 {len(text_items)} 个文本项")
            return text_items

        except Exception as e:
            self.logger.error(f"解析文档时发生错误: {str(e)}")
            raise

    def _filter_chunks(self, chunks: List) -> List:
        """
        过滤文档块，移除不需要的部分

        Args:
            chunks: 原始文档块列表

        Returns:
            过滤后的文档块列表
        """
        filtered_chunks = []

        for chunk in chunks:
            if self._should_exclude_chunk(chunk):
                self.logger.debug(
                    f"过滤掉块: {chunk.meta.headings[0] if chunk.meta.headings else '无标题'}"
                )
                continue
            filtered_chunks.append(chunk)

        return filtered_chunks

    def _should_exclude_chunk(self, chunk) -> bool:
        """
        判断是否应该排除某个文档块

        Args:
            chunk: 文档块

        Returns:
            True 如果应该排除，False 否则
        """
        # 检查是否有标题
        if not chunk.meta.headings:
            return False

        # 获取第一个标题并标准化
        heading = chunk.meta.headings[0].strip().casefold()

        # 检查是否在排除列表中
        return heading in {h.casefold() for h in self.excluded_headings}

    def _extract_text_items(self, chunks: List) -> List[Dict[str, Any]]:
        """
        从文档块中提取文本和页码信息

        Args:
            chunks: 文档块列表

        Returns:
            包含文本和页码的字典列表
        """
        text_items = []

        for chunk in chunks:
            try:
                # 提取文本
                text = chunk.text.strip()
                if not text:  # 跳过空文本
                    continue

                # 提取页码
                page_no = self._extract_page_number(chunk)

                text_items.append(
                    {
                        "text": text,
                        "page_idx": page_no,
                        "headings": chunk.meta.headings if chunk.meta.headings else [],
                    }
                )

            except Exception as e:
                self.logger.warning(f"提取文本项时出错: {str(e)}")
                continue

        return text_items

    def _extract_page_number(self, chunk) -> Optional[int]:
        """
        从文档块中提取页码

        Args:
            chunk: 文档块

        Returns:
            页码，如果无法提取则返回 None
        """
        try:
            if (
                chunk.meta.doc_items
                and chunk.meta.doc_items[0].prov
                and chunk.meta.doc_items[0].prov[0].page_no is not None
            ):
                return chunk.meta.doc_items[0].prov[0].page_no
        except (AttributeError, IndexError):
            pass

        return None

    def add_excluded_heading(self, heading: str) -> None:
        """
        添加需要排除的标题

        Args:
            heading: 要排除的标题
        """
        self.excluded_headings.add(heading.strip().casefold())
        self.logger.info(f"添加排除标题: {heading}")

    def remove_excluded_heading(self, heading: str) -> None:
        """
        移除排除的标题

        Args:
            heading: 要移除的标题
        """
        self.excluded_headings.discard(heading.strip().casefold())
        self.logger.info(f"移除排除标题: {heading}")

    def get_excluded_headings(self) -> Set[str]:
        """
        获取当前排除的标题列表

        Returns:
            排除的标题集合
        """
        return self.excluded_headings.copy()


# 使用示例
if __name__ == "__main__":
    # 创建解析器实例
    parser = PDFDocumentParser()

    # 可以添加更多要排除的标题
    parser.add_excluded_heading("acknowledgments")
    parser.add_excluded_heading("appendix")

    try:
        # 解析文档
        input_path = Path("./examples/2.Angelone.pdf")
        text_items = parser.parse_document(input_path)

        # 打印结果
        print(f"解析完成，共提取 {len(text_items)} 个文本块")
        for i, item in enumerate(text_items[:10]):  # 只显示前3个
            print(f"\n块 {i + 1}:")
            print(f"页码: {item['page_idx']}")
            print(f"标题: {item['headings']}")
            print(f"文本: {item['text'][:100]}...")

    except Exception as e:
        print(f"解析失败: {e}")
