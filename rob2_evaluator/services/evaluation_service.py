from typing import List, Dict, Any, Optional
from rob2_evaluator.agents.aggregator import Aggregator
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from rob2_evaluator.factories import DomainAgentFactory
import logging


class EvaluationService:
    """评估服务，负责协调分析类型判断和专家代理评估过程"""

    def __init__(
        self,
        analysis_type_agent: Optional[AnalysisTypeAgent] = None,
        aggregator: Optional[Aggregator] = None,
    ):
        self.analysis_type_agent = analysis_type_agent or AnalysisTypeAgent()
        self.aggregator = aggregator or Aggregator()
        self.domain_agents = None

    def evaluate(self, content_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行评估流程"""
        # 首先推断分析类型
        analysis_type = self.analysis_type_agent.infer_analysis_type(content_items)
        logging.info(f"推断的 Domain 2 分析类型: {analysis_type}")

        # 根据分析类型创建领域代理
        if not self.domain_agents:
            self.domain_agents = DomainAgentFactory.create_agents(analysis_type)

        # 执行领域评估
        domain_results = [agent.evaluate(content_items) for agent in self.domain_agents]

        # 汇总评估结果
        overall_result = self.aggregator.evaluate(domain_results)
        domain_results.append(overall_result)

        return domain_results
