from typing import List, Dict, Any, Optional
from rob2_evaluator.agents.aggregator import Aggregator
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from rob2_evaluator.factories import DomainAgentFactory
from concurrent.futures import ThreadPoolExecutor, as_completed
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

        # 多线程并发执行领域评估，结果顺序与 domain_agents 保持一致
        results: List[Dict[str, Any]] = [None] * len(self.domain_agents)  # type: ignore
        with ThreadPoolExecutor() as executor:
            future_to_idx = {
                executor.submit(agent.evaluate, content_items): idx
                for idx, agent in enumerate(self.domain_agents)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                result = future.result()
                results[idx] = result
        # 类型安全：过滤掉 None（理论上不会有）
        results = [r for r in results if r is not None]

        # 汇总评估结果
        overall_result = self.aggregator.evaluate(results)
        results.append(overall_result)

        return results
