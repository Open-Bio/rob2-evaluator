from typing import List, Dict, Any


class Aggregator:
    """
    汇总专家，根据ROB2官方规则对各Domain结果进行总体风险判定。
    适配新版 domain agent 输出结构。
    """

    # MIN_SOME_CONCERNS_FOR_HIGH_RISK 相关逻辑已删除。
    # 原先关于“多个‘一些担忧’领域导致总体‘高风险’”的规则及其具体化实现已被移除。

    def evaluate(self, domain_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        严格按照ROB2官方指南推荐的算法进行总体风险判定：

        1.  若任一领域被判定为“高风险 (High risk)”，则总体偏倚风险为“高风险”。
        2.  若所有领域均被判定为“低风险 (Low risk)”（并且没有领域为“高风险”），
            则总体偏倚风险为“低风险”。
        3.  若至少一个领域被判定为“一些担忧 (Some concerns)”（并且不满足上述导致
            “高风险”或所有领域均为“低风险”的条件），则总体偏倚风险为“一些担忧”。
        4.  如果没有提供领域评估结果，则判定为“无法评估 (Not applicable)”。

        参考 Cochrane Handbook for Systematic Reviews of Interventions version 6.4 (updated August 2023),
        Chapter 7, Section 7.7.1. （注意：原先关于多个“一些担忧”累积效应导致“高风险”的
        具体化规则已从此实现中移除。）
        """
        if not domain_results:
            return {
                "domain": "Overall risk of bias",
                "judgement": {"overall": "Not applicable"},
                "reasoning": "没有提供领域评估结果，无法进行总体偏倚风险评估。",
                "evidence": [],
            }

        risks = []
        evidence_list = []
        is_any_high_risk = False

        for result in domain_results:
            domain_name = result.get("domain", "Unknown domain")
            overall_judgment = result.get("overall", {})
            # 假设输入的 risk 总是 "Low risk", "Some concerns", 或 "High risk"
            risk_level = overall_judgment.get(
                "risk", "Some concerns"
            )  # 默认值以防万一，但应确保输入规范

            risks.append(risk_level)
            evidence_list.append({"domain": domain_name, "risk": risk_level})

            if risk_level == "High risk":
                is_any_high_risk = True
            # 'Some concerns' 计数相关的逻辑已移除

        overall_risk = "Not yet determined"
        reasoning = ""

        # 规则 1: 任一domain为High risk (来自 RoB 2 算法第一步)
        if is_any_high_risk:
            overall_risk = "High risk"
            reasoning = "由于至少一个偏倚领域被判定为“高风险 (High risk)”，因此总体偏倚风险被判定为“高风险”。"
        # 规则 2: 所有domain为Low risk (来自 RoB 2 算法第二步, 前提是没有High risk)
        elif all(r == "Low risk" for r in risks):
            overall_risk = "Low risk"
            reasoning = "由于所有偏倚领域均被判定为“低风险 (Low risk)”，因此总体偏倚风险被判定为“低风险”。"
        # 规则 3: 至少一个 Some concerns (来自 RoB 2 算法第三步主要条件，且不满足上述导致 High risk 或 Low risk 的条件)
        #   原先的规则3 (多个Some concerns导致High risk) 已被移除。
        elif any(r == "Some concerns" for r in risks):
            overall_risk = "Some concerns"
            reasoning = (
                "由于至少一个偏倚领域被判定为“一些担忧 (Some concerns)”，且不满足导致总体“高风险”或“低风险”的条件，"
                "因此总体偏倚风险被判定为“一些担忧”。"
            )
        # 规则 4: 其他情况 (理论上，如果输入规范，此分支不应轻易到达)
        # 例如，如果所有领域都不是 "Low risk", "Some concerns", "High risk" 中的任何一个。
        # 或者列表非空，但所有风险都不是这三者，这表示输入数据可能有问题。
        else:
            # 如果所有领域都被评估，且其风险等级是预期的三种之一，则不应到达此处。
            # 如果到达此处，可能表示输入数据不完整或存在非标准风险等级。
            # 为了程序的健壮性，提供一个审慎的判断。
            # 在RoB2的上下文中，当信息不足或存在不确定性时，“一些担忧”通常是比“低风险”更安全保守的默认判断。
            # 但更准确的可能是“无法确定”或提示检查输入。
            overall_risk = "Some concerns"  # 或者 "Undetermined due to unexpected/incomplete input"
            reasoning = (
                "无法根据明确规则判定总体风险，综合判定为“一些担忧 (Some concerns)”。"
                "请检查各领域评估结果是否完整且使用了标准的风险等级（Low risk, Some concerns, High risk）。"
            )

        return {
            "domain": "Overall risk of bias",
            "judgement": {"overall": overall_risk},
            "reasoning": reasoning,
            "evidence": evidence_list,
        }
