from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any


class EntryAgent:
    """
    入口专家：对原始json数组进行粗过滤，使用LLM判断每项是否与ROB2主题相关。
    相关项及其前后各1项一并保留，保证原文结构。
    """

    def __init__(
        self,
        context_window: int = 1,
        model_name="gemma3:27b",
        model_provider=ModelProvider.OLLAMA,
    ):
        self.context_window = context_window
        self.model_name = model_name
        self.model_provider = model_provider

    def is_relevant_llm(self, item: Dict[str, Any]) -> bool:
        prompt = f"""
You are an expert in risk of bias assessment for randomized controlled trials (ROB2 framework). 
Given the following text, answer with 'yes' if it is relevant to ROB2 risk of bias assessment (randomization, allocation, intervention, baseline, outcome, measurement, missing data, analysis, group, trial, etc.), otherwise answer 'no'.

Text:
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

    def filter_relevant(
        self, content_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        relevant_indices = set()
        for idx, item in enumerate(content_list):
            if self.is_relevant_llm(item):
                for offset in range(-self.context_window, self.context_window + 1):
                    neighbor_idx = idx + offset
                    if 0 <= neighbor_idx < len(content_list):
                        relevant_indices.add(neighbor_idx)
        return [content_list[i] for i in sorted(relevant_indices)]
