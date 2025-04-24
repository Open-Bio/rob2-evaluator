from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from pydantic import BaseModel
from typing import List, Dict, Any, Literal, Optional


class DeviationJudgement(BaseModel):
    analysis_type: Literal["assignment", "adherence"]
    q2_1: str
    q2_2: str
    q2_3: str
    q2_4: str
    q2_5: str
    q2_6: str
    q2_7: Optional[str] = None  # 修改为可选字段
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainDeviationAgent:
    """Domain 2: Deviations from intended interventions expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        self.model_name = model_name
        self.model_provider = model_provider

    def evaluate(
        self, items: List[Dict[str, Any]], analysis_type: str = "assignment"
    ) -> Dict[str, Any]:
        if analysis_type not in ["assignment", "adherence"]:
            raise ValueError("analysis_type must be either 'assignment' or 'adherence'")

        prompt = self._build_prompt(items, analysis_type)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=DeviationJudgement,
        )

        # 构建返回结果，只包含相关问题的判定
        judgement = {
            "analysis_type": analysis_type,
            "q2_1": result.q2_1,
            "q2_2": result.q2_2,
            "q2_3": result.q2_3,
            "q2_4": result.q2_4,
            "q2_5": result.q2_5,
            "q2_6": result.q2_6,
            "overall": result.overall,
        }
        if analysis_type == "assignment":
            judgement["q2_7"] = result.q2_7

        return {
            "domain": "Deviations from intended interventions",
            "judgement": judgement,
            "reasoning": result.reasoning,
            "evidence": result.evidence,
        }

    def _build_prompt(self, items: List[Dict[str, Any]], analysis_type: str) -> str:
        context = "\n".join(
            [
                f"[Page {item.get('page_idx', '?')}] {item.get('text', '')}"
                for item in items
            ]
        )

        prompt = f"""
You are an expert in risk of bias assessment for randomized controlled trials (ROB2 framework). 
Analyzing Domain 2: Deviations from intended interventions ({analysis_type} path).

Carefully review the following extracted study content (with page numbers):

{context}

Answer the following signalling questions strictly with one of: Low / High / Some concerns.

2.1 Were participants aware of their assigned intervention during the trial?
2.2 Were carers and people delivering the interventions aware of participants' assigned intervention during the trial?
"""

        if analysis_type == "assignment":
            prompt += """
2.3 Were there deviations from the intended intervention that arose because of the trial context?
2.4 Were these deviations likely to have affected the outcome?
2.5 Were these deviations from intended intervention balanced between groups?
2.6 Was an appropriate analysis used to estimate the effect of assignment to intervention?
2.7 Was there potential for a substantial impact of the failure to analyse participants in the group to which they were randomized?

Judgement guide:
- Low risk of bias: No deviations, or minor deviations balanced between groups, with appropriate analysis
- High risk of bias: Major deviations not balanced between groups, or inappropriate analysis
- Some concerns: Minor unbalanced deviations, or some concerns about analysis
"""
        else:  # adherence
            prompt += """
2.3 Were important non-protocol interventions balanced across intervention groups?
2.4 Were there failures in implementing the intervention that could have affected the outcome?
2.5 Was there non-adherence to the assigned intervention regimen that could have affected participants' outcomes?
2.6 Was an appropriate analysis used to estimate the effect of adhering to the intervention?

Judgement guide:
- Low risk of bias: Good intervention adherence, or appropriate analysis accounting for non-adherence
- High risk of bias: Poor adherence likely affecting outcomes, or inappropriate analysis
- Some concerns: Some non-adherence, but impact unclear or partially addressed in analysis
"""

        prompt += f"""
Return a JSON object with:
  "analysis_type": "{analysis_type}",
  "q2_1": "Low/High/Some concerns",
  "q2_2": "Low/High/Some concerns",
  "q2_3": "Low/High/Some concerns",
  "q2_4": "Low/High/Some concerns",
  "q2_5": "Low/High/Some concerns",
  "q2_6": "Low/High/Some concerns",
  "q2_7": "Low/High/Some concerns" (only for assignment path),
  "overall": "Low/High/Some concerns",
  "reasoning": "Concise justification in English",
  "evidence": [List of {{"page_idx": number, "text": "relevant text"}}]
"""
        return prompt
