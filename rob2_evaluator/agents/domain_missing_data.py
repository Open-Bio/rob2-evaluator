from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from pydantic import BaseModel
from typing import List, Dict, Any


class MissingDataJudgement(BaseModel):
    q3_1: str
    q3_2: str
    q3_3: str
    q3_4: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainMissingDataAgent:
    """Domain 3: Missing outcome data expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(self, items: List[Dict[str, Any]]):
        prompt = self._build_prompt(items)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=MissingDataJudgement,
        )
        return {
            "domain": "Missing outcome data",
            "judgement": {
                "q3_1": result.q3_1,
                "q3_2": result.q3_2,
                "q3_3": result.q3_3,
                "q3_4": result.q3_4,
                "overall": result.overall,
            },
            "reasoning": result.reasoning,
            "evidence": result.evidence,
        }

    def _build_prompt(self, items):
        context = "\n".join(
            [
                f"[Page {item.get('page_idx', '?')}] {item.get('text', '')}"
                for item in items
            ]
        )
        return f"""
You are an expert in risk of bias assessment for randomized controlled trials (ROB2 framework). Carefully review the following extracted study content (with page numbers):

{context}

For the domain 'Missing outcome data', answer the following signalling questions. For each, respond strictly with one of: Low / High / Some concerns.

3.1 Were data for this outcome available for all, or nearly all, participants randomized?
3.2 Is there evidence that the result was not biased by missing outcome data?
3.3 Could missingness in the outcome depend on its true value?
3.4 Is it likely that missingness in the outcome depended on its true value?

Judgement guide for Domain 3:
- Low risk of bias: Nearly complete outcome data (>95%) OR evidence that missing data did not bias results
- High risk of bias: Missing data likely depends on true values, OR inappropriate handling of missing data
- Some concerns: Some missing data without clear evidence about its impact on results

Return a JSON object with the following fields:
  q3_1, q3_2, q3_3, q3_4: (Low/High/Some concerns)
  overall: (Low/High/Some concerns, following the guide above)
  reasoning: (Concise justification for your answers, in English)
  evidence: (A list of objects, each with 'page_idx' and 'text', showing the most relevant supporting content)
Strictly use only the allowed options for all judgements.
"""
