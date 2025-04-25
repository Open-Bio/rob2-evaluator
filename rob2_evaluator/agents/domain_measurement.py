from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainMeasurementAgent(DomainAgent):
    def __init__(self, model_name="gemma3", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.MEASUREMENT, model_name, model_provider)
