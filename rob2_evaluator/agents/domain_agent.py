from rob2_evaluator.schema.rob2_schema import (
    DOMAIN_SCHEMAS,
    GenericDomainJudgement,
)
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any


class DomainAgent:
    def __init__(
        self,
        domain_key: str,
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    ):
        self.domain_key = domain_key
        self.schema = DOMAIN_SCHEMAS[domain_key]
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(self, items: List[Dict[str, Any]]):
        signals_schema = self.schema["signals"]
        prompt = self._build_prompt(items, signals_schema)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=GenericDomainJudgement,
            domain_key=self.domain_key,  # 添加domain_key参数
        )
        # 输出为表格友好格式
        return {
            "domain": self.schema["domain_name"],
            "signals": {
                k: {"answer": v.answer, "reason": v.reason, "evidence": v.evidence}
                for k, v in result.signals.items()
            },
            "overall": {
                "risk": result.overall.risk,
                "reason": result.overall.reason,
                "evidence": result.overall.evidence,
            },
        }

    def _build_prompt(self, items, signals_schema):
        context = "\n".join(
            [
                f"[Page {item.get('page_idx', '?')}] {item.get('text', '')}"
                for item in items
            ]
        )
        signal_questions = "\n".join(f"{s['id']}: {s['text']}" for s in signals_schema)
        signal_options = signals_schema[0]["options"]
        domain_options = self.schema["domain_options"]
        signals_json = ",\n  ".join(
            [
                f'"{s["id"]}": {{"answer": "{"/".join(signal_options)}", "reason": "...", "evidence": [{{"page_idx": int, "text": "..."}}, ...]}}'
                for s in signals_schema
            ]
        )
        domain_title = self.schema["domain_name"]
        prompt = f"""
You are an expert in risk of bias assessment for randomized controlled trials (ROB2 framework). Carefully review the following extracted study content (with page numbers):\n\n{context}\n\nFor the domain '{domain_title}', answer the following signalling questions. For each, respond strictly with one of: {"/".join(signal_options)}.\n\n{signal_questions}\n\nDomain-level risk of bias judgement (overall):\n- {"\n- ".join(domain_options)}\n\nReturn a JSON object with the following structure:\n{{\n  {signals_json},\n  "overall": {{"risk": "{"/".join(domain_options)}", "reason": "...", "evidence": [{{"page_idx": int, "text": "..."}}, ...]}}\n}}\nStrictly use only the allowed options for all answers.\n"""
        return prompt
