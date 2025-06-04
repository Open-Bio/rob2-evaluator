import pytest 
from rob2_evaluator.agents.aggregator import Aggregator

# 辅助函数创建领域结果，使测试更简洁
def create_domain_result(domain_name: str, risk_level: str) -> dict:
    return {"domain": domain_name, "overall": {"risk": risk_level}}

class TestAggregator:

    def test_high_risk_due_to_one_high_domain(self):
        """
        测试规则1：任一领域为 "High risk"，则总体为 "High risk"。
        """
        domain_results = [
            create_domain_result("Domain 1: Randomization process", "Low risk"),
            create_domain_result("Domain 2: Deviations from intended interventions", "High risk"),
            create_domain_result("Domain 3: Missing outcome data", "Some concerns"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "High risk"
        assert "由于至少一个偏倚领域被判定为“高风险 (High risk)”" in result["reasoning"]
        assert len(result["evidence"]) == 3
        assert {"domain": "Domain 2: Deviations from intended interventions", "risk": "High risk"} in result["evidence"]

    def test_low_risk_all_domains_low(self):
        """
        测试规则2：所有领域均为 "Low risk"，则总体为 "Low risk"。
        """
        domain_results = [
            create_domain_result("Domain 1: Randomization process", "Low risk"),
            create_domain_result("Domain 2: Deviations from intended interventions", "Low risk"),
            create_domain_result("Domain 3: Missing outcome data", "Low risk"),
            create_domain_result("Domain 4: Measurement of the outcome", "Low risk"),
            create_domain_result("Domain 5: Selection of the reported result", "Low risk"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Low risk"
        assert "由于所有偏倚领域均被判定为“低风险 (Low risk)”" in result["reasoning"]
        assert len(result["evidence"]) == 5

    def test_some_concerns_when_one_domain_is_some_concerns(self):
        """
        测试规则3：至少一个 "Some concerns"，且不满足其他导致 "High risk" 或 "Low risk" 的条件。
        (例如，1个 "Some concerns"，其余 "Low risk")
        """
        domain_results = [
            create_domain_result("Domain 1: Randomization process", "Low risk"),
            create_domain_result("Domain 2: Missing outcome data", "Some concerns"),
            create_domain_result("Domain 3: Measurement of the outcome", "Low risk"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Some concerns"
        assert "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert "不满足导致总体“高风险”或“低风险”的条件" in result["reasoning"]
        assert len(result["evidence"]) == 3

    def test_some_concerns_multiple_some_concerns(self):
        """
        测试：多个 "Some concerns" 但无 "High risk"，总体为 "Some concerns"。
        """
        domain_results = [
            create_domain_result("Domain SC 1", "Some concerns"),
            create_domain_result("Domain SC 2", "Some concerns"),
            create_domain_result("Domain LR 1", "Low risk"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Some concerns"
        assert "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert len(result["evidence"]) == 3

    def test_high_risk_takes_precedence_over_multiple_some_concerns(self):
        """
        测试规则1优先：即使有多个 "Some concerns"，但只要有一个 "High risk"，结果仍为 "High risk"。
        """
        domain_results = [
            create_domain_result("Domain High", "High risk"),
            create_domain_result("Domain SC 1", "Some concerns"),
            create_domain_result("Domain SC 2", "Some concerns"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "High risk"
        assert "由于至少一个偏倚领域被判定为“高风险 (High risk)”" in result["reasoning"]

    def test_not_applicable_for_empty_domain_results(self):
        """
        测试规则4：当领域结果列表为空时，总体评估为 "Not applicable"。
        """
        domain_results = []
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Not applicable"
        assert "没有提供领域评估结果" in result["reasoning"]
        assert len(result["evidence"]) == 0

    def test_all_some_concerns(self):
        """
        测试：所有领域都是 "Some concerns" 时，且无 High risk，总体为 "Some concerns"。
        """
        domain_results = [
            create_domain_result("Domain SC 1", "Some concerns"),
            create_domain_result("Domain SC 2", "Some concerns"),
            create_domain_result("Domain SC 3", "Some concerns"),
        ]
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Some concerns"
        assert "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert len(result["evidence"]) == 3
