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

    def test_high_risk_due_to_multiple_some_concerns(self):
        """
        测试规则3：MIN_SOME_CONCERNS_FOR_HIGH_RISK (默认为3) 个或更多 "Some concerns" 导致 "High risk"。
        """
        # 使用 Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK 来确保测试与类的定义同步
        threshold = Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK
        domain_results = []
        for i in range(threshold):
            domain_results.append(create_domain_result(f"Domain {i+1}", "Some concerns"))
        domain_results.append(create_domain_result(f"Domain {threshold+1}", "Low risk")) # 添加一个低风险，确保不是所有都Some concerns

        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "High risk"
        assert f"由于存在 {threshold} 个或更多偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert "其累积效应导致总体偏倚风险被判定为“高风险”" in result["reasoning"]
        assert len(result["evidence"]) == threshold + 1

    def test_some_concerns_when_one_domain_is_some_concerns(self):
        """
        测试规则4：至少一个 "Some concerns"，且不满足其他导致 "High risk" 或 "Low risk" 的条件。
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

    def test_some_concerns_multiple_some_concerns_below_threshold_for_high(self):
        """
        测试规则4：多个 "Some concerns" 但数量少于 MIN_SOME_CONCERNS_FOR_HIGH_RISK，且无 "High risk"。
        """
        if Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK <= 1:
            pytest.skip("Test not applicable if threshold for high risk from some concerns is 1 or less.")

        num_some_concerns = Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK - 1
        domain_results = []
        for i in range(num_some_concerns):
            domain_results.append(create_domain_result(f"Domain SC {i+1}", "Some concerns"))
        domain_results.append(create_domain_result("Domain LR 1", "Low risk"))

        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Some concerns"
        assert "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert len(result["evidence"]) == num_some_concerns + 1

    def test_high_risk_takes_precedence_over_multiple_some_concerns(self):
        """
        测试规则1优先：即使有多个 "Some concerns"，但只要有一个 "High risk"，结果仍为 "High risk"。
        """
        threshold = Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK
        domain_results = [create_domain_result("Domain High", "High risk")]
        for i in range(threshold):
            domain_results.append(create_domain_result(f"Domain SC {i+1}", "Some concerns"))

        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "High risk"
        assert "由于至少一个偏倚领域被判定为“高风险 (High risk)”" in result["reasoning"]

    def test_not_applicable_for_empty_domain_results(self):
        """
        测试规则5：当领域结果列表为空时，总体评估为 "Not applicable"。
        """
        domain_results = []
        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Not applicable"
        assert "没有提供领域评估结果" in result["reasoning"]
        assert len(result["evidence"]) == 0

    def test_all_some_concerns_less_than_threshold_for_high(self):
        """
        测试：如果所有领域都是 "Some concerns"，但数量少于触发 "High risk" 的阈值。
        """
        if Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK <= 1:
            pytest.skip("Test not applicable if threshold for high risk from some concerns is 1 or less.")

        num_some_concerns = Aggregator.MIN_SOME_CONCERNS_FOR_HIGH_RISK - 1
        domain_results = []
        for i in range(num_some_concerns):
            domain_results.append(create_domain_result(f"Domain SC {i+1}", "Some concerns"))

        agg = Aggregator()
        result = agg.evaluate(domain_results)
        assert result["judgement"]["overall"] == "Some concerns"
        assert "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”" in result["reasoning"]
        assert len(result["evidence"]) == num_some_concerns
