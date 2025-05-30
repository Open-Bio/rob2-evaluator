from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainSelectionAgent(DomainAgent):
    """Domain 5: Selection of the reported result expert using LLM for structured ROB2 assessment."""

    def __init__(self):
        super().__init__(DomainKey.SELECTION)
