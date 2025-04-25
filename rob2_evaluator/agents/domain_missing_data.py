from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
    SignalJudgement,
    DomainJudgement,
    GenericDomainJudgement,
)
from pydantic import BaseModel
from typing import List, Dict, Any


class DomainMissingDataAgent(DomainAgent):
    """Domain 3: Missing outcome data expert using LLM for structured ROB2 assessment."""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.MISSING_DATA, model_name, model_provider)
