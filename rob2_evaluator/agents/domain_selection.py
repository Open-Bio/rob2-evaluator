from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from pydantic import BaseModel
from typing import List, Dict, Any


class SelectionJudgement(BaseModel):
    q5_1: str
    q5_2: str
    q5_3: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainSelectionAgent:
    """Domain 5: Selection of the reported result expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(self, items: List[Dict[str, Any]]):
        prompt = self._build_prompt(items)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=SelectionJudgement,
        )
        return {
            "domain": "Selection of the reported result",
            "judgement": {
                "q5_1": result.q5_1,
                "q5_2": result.q5_2,
                "q5_3": result.q5_3,
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

For the domain 'Selection of the reported result', answer the following signalling questions. For each, respond strictly with one of: Low / High / Some concerns.

5.1 Were the data that produced this result analysed in accordance with a pre-specified analysis plan?
5.2 Was the result selected from multiple eligible outcome measurements?
5.3 Was the result selected from multiple eligible analyses of the data?

Judgement guide for Domain 5:
- Low risk of bias:
  * Analysis follows pre-specified plan AND
  * No selection from multiple measurements/analyses OR
  * Appropriate selection methods used
- High risk of bias:
  * Selection from multiple measurements/analyses likely to have produced biased results OR
  * Major deviations from pre-specified analysis plan
- Some concerns:
  * Some concerns about selective reporting OR
  * Insufficient information about analysis plan

Return a JSON object with the following fields:
  q5_1, q5_2, q5_3: (Low/High/Some concerns)
  overall: (Low/High/Some concerns, following the guide above)
  reasoning: (Concise justification for your answers, in English)
  evidence: (A list of objects, each with 'page_idx' and 'text', showing the most relevant supporting content)
Strictly use only the allowed options for all judgements.
"""
