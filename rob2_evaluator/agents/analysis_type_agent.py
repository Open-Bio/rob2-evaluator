from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any
from rob2_evaluator.config.model_config import ModelConfig
from typing import Optional


class AnalysisTypeAgent:
    """
    用于自动判断Domain 2分析类型（assignment 或 adherence）。
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ):
        config = ModelConfig()
        # 优先使用传入的参数，其次使用配置值
        self.model_name = model_name or config.get_model_name()
        self.model_provider = model_provider or config.get_model_provider()

    def infer_analysis_type(self, items: List[Dict[str, Any]]) -> str:
        context = "\n".join([item.get("text", "") for item in items])
        prompt = f"""
You are an expert in ROB2 risk of bias assessment.
Given the following study content, determine which analysis type is most appropriate for Domain 2:
- 'assignment' (effect of assignment to intervention, i.e., intention-to-treat analysis)
- 'adherence' (effect of adhering to intervention, i.e., per-protocol or as-treated analysis)

Text:
{context}

Answer with only 'assignment' or 'adherence'.
"""
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=None,
        )
        answer = str(result).strip().lower()
        return "adherence" if "adherence" in answer else "assignment"
