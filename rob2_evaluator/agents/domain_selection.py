from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import DomainKey
from pydantic import BaseModel
from typing import List, Dict, Any


class SelectionJudgement(BaseModel):
    q5_1: str
    q5_2: str
    q5_3: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainSelectionAgent(DomainAgent):
    """Domain 5: Selection of the reported result expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.SELECTION, model_name, model_provider)
