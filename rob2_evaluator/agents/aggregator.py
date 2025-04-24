from typing import List, Dict, Any


class Aggregator:
    """汇总专家，根据ROB2官方规则对各Domain结果进行总体风险判定"""

    def evaluate(self, domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根据ROB2规则进行总体风险判定：
        1. 如果任一Domain为High risk，总体为High risk
        2. 如果所有Domain为Low risk，总体为Low risk
        3. 其他情况为Some concerns
        """
        # 收集所有Domain的overall判定
        domain_judgements = [
            result.get("judgement", {}).get("overall", "Some concerns")
            for result in domain_results
        ]

        # ROB2规则判定总体风险
        if any(j == "High" for j in domain_judgements):
            overall = "High"
        elif all(j == "Low" for j in domain_judgements):
            overall = "Low"
        else:
            overall = "Some concerns"

        # 构建详细理由
        reasoning = []
        for result in domain_results:
            domain = result.get("domain", "Unknown domain")
            judgement = result.get("judgement", {}).get("overall", "Some concerns")
            reasoning.append(f"{domain}: {judgement}")

        return {
            "domain": "Overall risk of bias",
            "judgement": {"overall": overall},
            "reasoning": ";\n".join(reasoning),
            "evidence": [
                {"domain": r.get("domain"), "judgement": r.get("judgement", {})}
                for r in domain_results
            ],
        }
