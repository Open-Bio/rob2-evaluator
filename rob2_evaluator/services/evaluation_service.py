from typing import List, Dict, Any, Optional
from rob2_evaluator.agents.aggregator import Aggregator
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from rob2_evaluator.agents.single_domain_reviewer import (
    DomainReviewerFactory,
)
from rob2_evaluator.factories import DomainAgentFactory
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os


class EvaluationService:
    """评估服务，负责协调分析类型判断和专家代理评估过程"""

    def __init__(
        self,
        analysis_type_agent: Optional[AnalysisTypeAgent] = None,
        aggregator: Optional[Aggregator] = None,
        enable_review: Optional[bool] = None,
        review_standards: Optional[Dict[str, str]] = None,
    ):
        self.analysis_type_agent = analysis_type_agent or AnalysisTypeAgent()
        self.aggregator = aggregator or Aggregator()

        # 从环境变量读取审查机制配置，默认启用
        if enable_review is None:
            env_enable_review = os.getenv("ENABLE_REVIEW", "true").lower()
            self.enable_review = env_enable_review in ("true", "1", "yes", "on")
        else:
            self.enable_review = enable_review

        # 创建专门的domain审查器
        if self.enable_review:
            if review_standards:
                self.domain_reviewers = DomainReviewerFactory.create_reviewers(
                    review_standards
                )
            else:
                # 使用默认标准创建审查器
                from rob2_evaluator.config.review_config import ReviewConfig

                config = ReviewConfig()
                self.domain_reviewers = DomainReviewerFactory.create_reviewers(
                    config.get_standards()
                )
        else:
            self.domain_reviewers = None

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

        # 审查和重写阶段：使用专门的domain审查器
        if self.enable_review and self.domain_reviewers:
            logging.info("开始专项审查和重写阶段...")
            reviewed_results = [None] * len(results)  # type: ignore

            # 并发执行审查和重写，使用专门的审查器
            with ThreadPoolExecutor() as executor:
                future_to_idx = {}
                for idx, result in enumerate(results):
                    # 从结果中提取domain_key
                    domain_key = result.get("domain_key")
                    if not domain_key:
                        logging.warning(f"结果 {idx + 1} 缺少domain_key，跳过审查")
                        reviewed_results[idx] = result
                        continue

                    # 获取对应的专项审查器
                    reviewer = self.domain_reviewers.get(domain_key)
                    if reviewer:
                        future = executor.submit(reviewer.review_and_revise, result)
                        future_to_idx[future] = idx
                    else:
                        # 如果没有对应的审查器，保持原结果
                        logging.warning(f"没有找到 {domain_key} 的专项审查器，跳过审查")
                        reviewed_results[idx] = result

                # 收集审查结果，保持原有顺序
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        reviewed_result = future.result()
                        reviewed_results[idx] = reviewed_result
                    except Exception as e:
                        logging.error(f"审查失败 (domain {idx + 1}): {e}")
                        # 如果审查失败，使用原始结果
                        reviewed_results[idx] = results[idx]

            # 过滤掉None值并更新results
            results = [r for r in reviewed_results if r is not None]
            logging.info(f"专项审查完成，处理了 {len(results)} 个domain结果")

        # 汇总评估结果
        overall_result = self.aggregator.evaluate(results)
        results.append(overall_result)

        return results
