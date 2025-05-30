from typing import List
from rob2_evaluator.agents.domain_agent import DomainAgent
from rob2_evaluator.agents.domain_randomization import DomainRandomizationAgent
from rob2_evaluator.agents.domain_deviation import (
    DomainDeviationAdherenceAgent,
    DomainDeviationAssignmentAgent,
)
from rob2_evaluator.agents.domain_measurement import DomainMeasurementAgent
from rob2_evaluator.agents.domain_selection import DomainSelectionAgent
from rob2_evaluator.agents.domain_missing_data import DomainMissingDataAgent


class DomainAgentFactory:
    """领域专家代理工厂"""

    @staticmethod
    def create_agents(analysis_type: str) -> List[DomainAgent]:
        """根据分析类型创建对应的领域专家代理列表"""
        base_agents = [
            DomainRandomizationAgent(),
            DomainMissingDataAgent(),
            DomainMeasurementAgent(),
            DomainSelectionAgent(),
        ]

        # 根据分析类型添加相应的偏差专家
        if analysis_type == "assignment":
            base_agents.insert(1, DomainDeviationAssignmentAgent())
        else:  # adherence
            base_agents.insert(1, DomainDeviationAdherenceAgent())

        return base_agents
