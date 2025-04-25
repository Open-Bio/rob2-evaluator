from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import (
    DomainAgent,
)
from typing import List, Dict, Any
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainDeviationAssignmentAgent(DomainAgent):
    """Domain 2: Deviations from intended interventions (effect of assignment) expert"""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.DEVIATION_ASSIGNMENT, model_name, model_provider)

    def evaluate(self, items: List[Dict[str, Any]], **kwargs):
        # 自动注入 analysis_type
        return super().evaluate(items, analysis_type="assignment")


class DomainDeviationAdherenceAgent(DomainAgent):
    """Domain 2: Deviations from intended interventions (effect of adherence) expert"""

    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.DEVIATION_ADHERENCE, model_name, model_provider)

    def evaluate(self, items: List[Dict[str, Any]], **kwargs):
        # 自动注入 analysis_type
        return super().evaluate(items, analysis_type="adherence")
