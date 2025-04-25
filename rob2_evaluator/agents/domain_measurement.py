from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from pydantic import BaseModel
from typing import List, Dict, Any
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
    SignalJudgement,
    DomainJudgement,
    GenericDomainJudgement,
)


class DomainMeasurementAgent(DomainAgent):
    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.MEASUREMENT, model_name, model_provider)
