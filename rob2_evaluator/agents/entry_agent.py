from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any
import re


class EntryAgent:
    """
    入口专家：对原始json数组进行粗过滤，使用LLM判断每项是否与ROB2主题相关。
    相关项及其前后各1项一并保留，保证原文结构。
    会在遇到参考文献部分时停止处理，并对短文本进行批量处理。
    """

    def __init__(
        self,
        context_window: int = 1,
        model_name="gemma3:27b",
        model_provider=ModelProvider.OLLAMA,
        short_text_threshold: int = 100,
        batch_size: int = 3,
    ):
        self.context_window = context_window
        self.model_name = model_name
        self.model_provider = model_provider
        self.short_text_threshold = short_text_threshold
        self.batch_size = batch_size

    def is_relevant_llm(self, item: Dict[str, Any]) -> bool:
        prompt = f"""
# Role
You are an expert reviewer specializing in ROB2 (Risk of Bias 2) assessment for randomized controlled trials.

# Task
Evaluate if the text is relevant to ROB2 risk of bias assessment.

# Context
The ROB2 tool evaluates bias in these domains:
- Randomization process
- Deviations from intended interventions
- Missing outcome data
- Measurement of outcomes
- Selection of reported results

# Limitations
- Answer only 'yes' or 'no'

# Examples
Relevant (yes): "Participants were randomly assigned to treatment groups using a computer-generated sequence."
Not relevant (no): "The study was conducted between January and June 2018."

# Text to evaluate:
{item.get("text", "")}

Answer only 'yes' or 'no'.
"""
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=None,
        )
        answer = str(result).strip().lower()
        return answer.startswith("yes")

    def is_references_section(self, item: Dict[str, Any]) -> bool:
        """检查当前项是否为参考文献部分的标题"""
        if item.get("text_level") == 1:
            text = item.get("text", "").strip()
            return bool(re.search(r"REFERENCES\s*", text, re.IGNORECASE))
        return False

    def filter_relevant(
        self, content_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        relevant_indices = set()
        i = 0

        while i < len(content_list):
            # 检查是否已到参考文献部分
            if self.is_references_section(content_list[i]):
                break

            current_item = content_list[i]
            current_text = current_item.get("text", "")

            # 处理短文本：批量合并评估
            if len(
                current_text
            ) < self.short_text_threshold and i + self.batch_size <= len(content_list):
                # 确保批次中没有参考文献部分
                if any(
                    self.is_references_section(content_list[j])
                    for j in range(i, i + self.batch_size)
                ):
                    break

                # 创建合并项目用于评估
                combined_text = "\n".join(
                    [
                        content_list[j].get("text", "")
                        for j in range(i, i + self.batch_size)
                    ]
                )
                combined_item = {"text": combined_text}

                if self.is_relevant_llm(combined_item):
                    # 如果合并项相关，所有包含项都视为相关
                    for j in range(i, i + self.batch_size):
                        for offset in range(
                            -self.context_window, self.context_window + 1
                        ):
                            neighbor_idx = j + offset
                            if 0 <= neighbor_idx < len(content_list):
                                relevant_indices.add(neighbor_idx)

                i += self.batch_size  # 跳过已处理的批次
            else:
                # 处理单个项目
                if self.is_relevant_llm(current_item):
                    for offset in range(-self.context_window, self.context_window + 1):
                        neighbor_idx = i + offset
                        if 0 <= neighbor_idx < len(content_list):
                            relevant_indices.add(neighbor_idx)

                i += 1  # 处理下一项

        return [content_list[i] for i in sorted(relevant_indices)]
