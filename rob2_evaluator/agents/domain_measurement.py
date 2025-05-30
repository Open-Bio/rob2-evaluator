from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainMeasurementAgent(DomainAgent):
    """Domain 2: Measurement of the outcome expert using LLM for structured ROB2 assessment."""

    def __init__(self):
        super().__init__(DomainKey.MEASUREMENT)
