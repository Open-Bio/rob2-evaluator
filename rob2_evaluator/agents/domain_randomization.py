from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import DomainKey
from pydantic import BaseModel
from typing import List, Dict, Any


class RandomizationJudgement(BaseModel):
    q1_1: str
    q1_2: str
    q1_3: str
    overall: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class DomainRandomizationAgent(DomainAgent):
    """Domain 1: Randomization process expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.RANDOMIZATION, model_name, model_provider)
