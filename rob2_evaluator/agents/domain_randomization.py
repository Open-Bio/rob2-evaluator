from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from pydantic import BaseModel
from typing import List, Dict, Any


class RandomizationJudgement(BaseModel):
    q1_1: str
    q1_2: str
    q1_3: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainRandomizationAgent:
    """Domain 1: Randomization process expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(self, items: List[Dict[str, Any]]):
        prompt = self._build_prompt(items)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=RandomizationJudgement,
        )
        return {
            "domain": "Randomization process",
            "judgement": {
                "q1_1": result.q1_1,
                "q1_2": result.q1_2,
                "q1_3": result.q1_3,
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

For the domain 'Randomization process', answer the following signalling questions. For each, respond strictly with one of: Low / High / Some concerns.

1.1 Was the allocation sequence random?
1.2 Was the allocation sequence concealed until participants were enrolled and assigned to interventions?
1.3 Did baseline differences between intervention groups suggest a problem with the randomization process?

Judgement guide for Domain 1:
- Low risk of bias: Random sequence, concealment of allocation, AND no baseline differences suggesting problems
- High risk of bias: Problems with sequence generation OR concealment, OR baseline differences suggesting problems
- Some concerns: If insufficient information about sequence generation or concealment

Return a JSON object with the following fields:
  q1_1, q1_2, q1_3: (Low/High/Some concerns)
  overall: (Low/High/Some concerns, following the guide above)
  reasoning: (Concise justification for your answers, in English)
  evidence: (A list of objects, each with 'page_idx' and 'text', showing the most relevant supporting content)
Strictly use only the allowed options for all judgements.
"""
