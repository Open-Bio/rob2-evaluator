from rob2_evaluator.agents.aggregator import Aggregator
from rob2_evaluator.agents.domain_randomization import DomainRandomizationAgent
from rob2_evaluator.agents.domain_deviation import (
    DomainDeviationAdherenceAgent,
    DomainDeviationAssignmentAgent,
)
from rob2_evaluator.agents.domain_measurement import DomainMeasurementAgent
from rob2_evaluator.agents.domain_selection import DomainSelectionAgent
from rob2_evaluator.agents.domain_missing_data import DomainMissingDataAgent
from rob2_evaluator.agents.entry_agent import EntryAgent
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from rob2_evaluator.utils.json_io import load_json
import logging
import json
import os
from jinja2 import Environment, FileSystemLoader


def render_report(results, output_path="report.html"):
    """渲染评估结果为HTML报告"""
    template_dir = os.path.join(os.path.dirname(__file__))
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("report_template.html.j2")
    from rob2_evaluator.schema.rob2_schema import DOMAIN_SCHEMAS

    html = template.render(results=results, domain_schemas=DOMAIN_SCHEMAS)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"评估报告已生成: {output_path}")


def process_single_file(input_path):
    content_list = load_json(input_path)
    # # 入口专家过滤
    entry_agent = EntryAgent()
    relevant_items = entry_agent.filter_relevant(content_list)
    # 自动推断Domain 2分析类型
    analysis_type_agent = AnalysisTypeAgent()
    analysis_type = analysis_type_agent.infer_analysis_type(relevant_items)
    logging.info(f"Inferred Domain 2 analysis type: {analysis_type}")

    if analysis_type == "assignment":
        # Domain 2 分析类型为 assignment
        domain_agents = [
            DomainRandomizationAgent(),
            DomainDeviationAssignmentAgent(),
            DomainMissingDataAgent(),
            DomainMeasurementAgent(),
            DomainSelectionAgent(),
        ]
    else:
        # Domain 2 分析类型为 adherence
        domain_agents = [
            DomainRandomizationAgent(),
            DomainDeviationAdherenceAgent(),
            DomainMissingDataAgent(),
            DomainMeasurementAgent(),
            DomainSelectionAgent(),
        ]

    domain_results = [agent.evaluate(relevant_items) for agent in domain_agents]

    # 汇总专家评估
    aggregator = Aggregator()
    overall_result = aggregator.evaluate(domain_results)

    # 将汇总结果添加到扁平化的结果数组中
    domain_results.append(overall_result)

    return domain_results


if __name__ == "__main__":
    result = process_single_file("examples/20.Gottlie.json")
    print(json.dumps(result, indent=4, ensure_ascii=False))
    # 渲染HTML报告
    render_report(result, output_path="report.html")
