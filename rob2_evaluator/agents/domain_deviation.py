from rob2_evaluator.agents.domain_agent import (
    DomainAgent,
)
from rob2_evaluator.schema.rob2_schema import (
    DomainKey,
)


class DomainDeviationAssignmentAgent(DomainAgent):
    """Domain 2: Deviations from intended interventions (effect of assignment) expert"""

    def __init__(self):
        super().__init__(DomainKey.DEVIATION_ASSIGNMENT)


class DomainDeviationAdherenceAgent(DomainAgent):
    """Domain 2: Deviations from intended interventions (effect of adherence) expert"""

    def __init__(self):
        super().__init__(DomainKey.DEVIATION_ADHERENCE)
