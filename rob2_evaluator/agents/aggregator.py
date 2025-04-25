from typing import List, Dict, Any


class Aggregator:
    """
    汇总专家，根据ROB2官方规则对各Domain结果进行总体风险判定。
    适配新版 domain agent 输出结构。
    """

    # 关键领域，权重更高
    KEY_DOMAINS = {"Randomization process", "Missing outcome data"}

    def evaluate(self, domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        严格按照ROB2官方规则进行总体风险判定：
        1. 任一domain为High risk，则overall为High risk
        2. 关键领域为Some concerns，则overall为Some concerns（若无High risk）
        3. ≥3个Some concerns，则overall为High risk
        4. 所有domain为Low risk，则overall为Low risk
        5. 其余情况为Some concerns
        """
        risks = []
        evidence = []
        key_domain_risks = []
        some_concerns_count = 0
        for result in domain_results:
            domain = result.get("domain", "Unknown domain")
            overall = result.get("overall", {})
            risk = overall.get("risk", "Some concerns")
            risks.append(risk)
            evidence.append({"domain": domain, "risk": risk})
            if domain in self.KEY_DOMAINS:
                key_domain_risks.append(risk)
            if risk == "Some concerns":
                some_concerns_count += 1

        # 1. 任一domain为High risk
        if any(r == "High risk" for r in risks):
            overall_risk = "High risk"
            reasoning = "存在高风险领域，整体判定为High risk。"
        # 2. 关键领域为Some concerns
        elif any(r == "Some concerns" for r in key_domain_risks):
            overall_risk = "Some concerns"
            reasoning = "关键领域存在Some concerns，整体判定为Some concerns。"
        # 3. ≥3个Some concerns
        elif some_concerns_count >= 3:
            overall_risk = "High risk"
            reasoning = "有3个及以上领域为Some concerns，整体判定为High risk。"
        # 4. 所有domain为Low risk
        elif all(r == "Low risk" for r in risks) and risks:
            overall_risk = "Low risk"
            reasoning = "所有领域均为Low risk，整体判定为Low risk。"
        # 5. 其余情况
        else:
            overall_risk = "Some concerns"
            reasoning = "综合各领域风险等级，整体判定为Some concerns。"

        return {
            "domain": "Overall risk of bias",
            "judgement": {"overall": overall_risk},
            "reasoning": reasoning,
            "evidence": evidence,
        }
