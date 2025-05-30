from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainRandomizationAgent(DomainAgent):
    """Domain 1: Randomization process expert using LLM for structured ROB2 assessment."""

    def __init__(self):
        super().__init__(DomainKey.RANDOMIZATION)
