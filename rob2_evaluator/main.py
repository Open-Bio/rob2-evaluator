from rob2_evaluator.agents.entry_agent import EntryAgent
from rob2_evaluator.agents.aggregator import Aggregator
from rob2_evaluator.agents.domain_randomization import DomainRandomizationAgent
from rob2_evaluator.agents.domain_deviation import DomainDeviationAgent
from rob2_evaluator.agents.domain_missing_data import DomainMissingDataAgent
from rob2_evaluator.agents.domain_measurement import DomainMeasurementAgent
from rob2_evaluator.agents.domain_selection import DomainSelectionAgent
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from rob2_evaluator.utils.json_io import load_json
import sys
import os
import argparse
import logging
import pandas as pd
from pathlib import Path
import json


def process_single_file(input_path):
    content_list = load_json(input_path)

    # 入口专家过滤
    entry_agent = EntryAgent()
    relevant_items = entry_agent.filter_relevant(content_list)

    # 自动推断Domain 2分析类型
    analysis_type_agent = AnalysisTypeAgent()
    analysis_type = analysis_type_agent.infer_analysis_type(relevant_items)
    logging.info(f"Inferred Domain 2 analysis type: {analysis_type}")

    # Domain专家评估
    domain_agents = [
        DomainRandomizationAgent(),
        # Domain 2使用统一的专家，指定分析类型
        DomainDeviationAgent(),
        DomainMissingDataAgent(),
        DomainMeasurementAgent(),
        DomainSelectionAgent(),
    ]
    domain_results = [
        agent.evaluate(relevant_items)
        if not isinstance(agent, DomainDeviationAgent)
        else agent.evaluate(relevant_items, analysis_type=analysis_type)
        for agent in domain_agents
    ]

    # 汇总专家评估
    aggregator = Aggregator()
    overall_result = aggregator.evaluate(domain_results)

    # 将汇总结果添加到扁平化的结果数组中
    domain_results.append(overall_result)

    return domain_results


def create_result_row(file_name, results, simplified=False):
    row = {"file_name": file_name}

    for result in results:
        domain = result["domain"]
        if simplified:
            row[f"{domain}_judgement"] = result["judgement"]["overall"]
        else:
            row[f"{domain}_judgement"] = result["judgement"]["overall"]
            row[f"{domain}_reasoning"] = result["reasoning"]
            if "evidence" in result:
                row[f"{domain}_evidence"] = json.dumps(
                    result["evidence"], ensure_ascii=False
                )
            if "analysis_type" in result.get("judgement", {}):
                row[f"{domain}_analysis_type"] = result["judgement"]["analysis_type"]

    return row


def main():
    parser = argparse.ArgumentParser(description="ROB2 Evaluation Tool")
    parser.add_argument("input_path", help="Input JSON file or directory path")
    parser.add_argument(
        "-o", "--output", help="Output file path for results (CSV format)"
    )
    parser.add_argument(
        "--simplified", action="store_true", help="Output simplified results"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    input_path = Path(args.input_path)
    results_data = []

    if input_path.is_file():
        if not input_path.suffix == ".json":
            logging.error("Input file must be JSON format")
            sys.exit(1)
        logging.info(f"Processing single file: {input_path}")
        results = process_single_file(str(input_path))
        results_data.append(
            create_result_row(input_path.name, results, args.simplified)
        )

    elif input_path.is_dir():
        logging.info(f"Processing directory: {input_path}")
        for json_file in input_path.glob("*.json"):
            logging.info(f"Processing file: {json_file}")
            try:
                results = process_single_file(str(json_file))
                results_data.append(
                    create_result_row(json_file.name, results, args.simplified)
                )
            except Exception as e:
                logging.error(f"Error processing {json_file}: {str(e)}")
                continue

    # 创建结果DataFrame
    results_df = pd.DataFrame(results_data)

    # 保存结果
    if args.output:
        results_df.to_csv(args.output, index=False)
        logging.info(f"Results saved to {args.output}")
    else:
        print("\nResults:")
        print(results_df.to_string())


if __name__ == "__main__":
    main()
