from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from pydantic import BaseModel
from typing import List, Dict, Any


class MeasurementJudgement(BaseModel):
    q4_1: str
    q4_2: str
    q4_3: str
    q4_4: str
    q4_5: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainMeasurementAgent:
    """Domain 4: Measurement of the outcome expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(self, items: List[Dict[str, Any]]):
        prompt = self._build_prompt(items)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=MeasurementJudgement,
        )
        return {
            "domain": "Measurement of the outcome",
            "judgement": {
                "q4_1": result.q4_1,
                "q4_2": result.q4_2,
                "q4_3": result.q4_3,
                "q4_4": result.q4_4,
                "q4_5": result.q4_5,
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

For the domain 'Measurement of the outcome', answer the following signalling questions. For each, respond strictly with one of: Low / High / Some concerns.

4.1 Was the method of measuring the outcome inappropriate?
4.2 Could measurement or ascertainment of the outcome have differed between intervention groups?
4.3 Were outcome assessors aware of the intervention received by study participants?
4.4 Could assessment of the outcome have been influenced by knowledge of intervention received?
4.5 Is it likely that assessment of the outcome was influenced by knowledge of intervention received?

Judgement guide for Domain 4:
- Low risk of bias: 
  * Appropriate outcome measurement methods AND
  * Outcome assessors blinded to intervention OR
  * Outcome measurement unlikely to be influenced by knowledge of intervention
- High risk of bias:
  * Inappropriate measurement methods OR
  * Different methods between groups OR
  * Unblinded assessment likely influenced by knowledge of intervention
- Some concerns:
  * Some problems with measurement methods OR
  * Unclear blinding status with potential for influence

Return a JSON object with the following fields:
  q4_1, q4_2, q4_3, q4_4, q4_5: (Low/High/Some concerns)
  overall: (Low/High/Some concerns, following the guide above)
  reasoning: (Concise justification for your answers, in English)
  evidence: (A list of objects, each with 'page_idx' and 'text', showing the most relevant supporting content)
Strictly use only the allowed options for all judgements.
"""
