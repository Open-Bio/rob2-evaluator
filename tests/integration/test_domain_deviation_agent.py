import pytest
from rich import print as rprint
from rob2_evaluator.agents.domain_deviation import (
    DomainDeviationAssignmentAgent,
    DomainDeviationAdherenceAgent,
)
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.utils.json_io import load_json
import json


def print_llm_response(result):
    """打印格式化的LLM响应"""
    rprint("\n[bold cyan]===== LLM Response Details =====[/bold cyan]")
    rprint(json.dumps(result, indent=2, ensure_ascii=False))
    rprint("[bold cyan]=============================[/bold cyan]\n")


def test_domain_deviation_assignment_integration():
    """测试Assignment子代理的正常情况"""
    test_content = load_json("examples/20.Gottlie.json")
    agent = DomainDeviationAssignmentAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    try:
        result = agent.evaluate(test_content)
        print_llm_response(result)

        # 结构验证
        assert "domain" in result
        assert (
            result["domain"]
            == "Risk of bias due to deviations from the intended interventions (effect of assignment)"
        )
        assert "signals" in result
        assert "overall" in result

        # Assignment类型应该有7个信号问题
        signals = result["signals"]
        for q_id in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6", "q2_7"]:
            assert q_id in signals
            assert "answer" in signals[q_id]
            assert signals[q_id]["answer"] in ["Y", "PY", "PN", "N", "NI"]
            assert "reason" in signals[q_id]
            assert isinstance(signals[q_id]["evidence"], list)

            rprint(f"\n[bold green]Signal {q_id} Assessment:[/bold green]")
            rprint(f"Answer: {signals[q_id]['answer']}")
            rprint(f"Reason: {signals[q_id]['reason']}")
            rprint("Evidence:")
            for e in signals[q_id]["evidence"]:
                rprint(f"- Page {e['page_idx']}: {e['text']}")

        assert result["overall"]["risk"] in ["Low risk", "Some concerns", "High risk"]

    except Exception as e:
        rprint(f"\n[bold red]Error during assignment evaluation:[/bold red] {str(e)}")
        raise


def test_domain_deviation_adherence_integration():
    """测试Adherence子代理的正常情况"""
    test_content = load_json("examples/20.Gottlie.json")
    agent = DomainDeviationAdherenceAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    try:
        result = agent.evaluate(test_content)
        print_llm_response(result)

        # 结构验证
        assert "domain" in result
        assert (
            result["domain"]
            == "Risk of bias due to deviations from the intended interventions (effect of adherence)"
        )
        assert "signals" in result
        assert "overall" in result

        # Adherence类型应该只有6个信号问题
        signals = result["signals"]
        for q_id in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6"]:
            assert q_id in signals
            assert "answer" in signals[q_id]
            assert signals[q_id]["answer"] in ["Y", "PY", "PN", "N", "NI"]
            assert "reason" in signals[q_id]
            assert isinstance(signals[q_id]["evidence"], list)

        # q2_7不应该存在
        assert "q2_7" not in signals

        assert result["overall"]["risk"] in ["Low risk", "Some concerns", "High risk"]

    except Exception as e:
        rprint(f"\n[bold red]Error during adherence evaluation:[/bold red] {str(e)}")
        raise


def test_domain_deviation_assignment_error_cases():
    """测试Assignment子代理的错误情况"""
    agent = DomainDeviationAssignmentAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    try:
        # 测试空输入
        empty_result = agent.evaluate([])
        rprint("\n[bold red]Empty Input Test (Assignment):[/bold red]")
        print_llm_response(empty_result)

        # 验证空输入结果结构
        assert "domain" in empty_result
        assert "signals" in empty_result
        assert "overall" in empty_result
        assert "q2_7" in empty_result["signals"]  # assignment类型特有的信号问题
        assert empty_result["overall"]["risk"] in [
            "Low risk",
            "Some concerns",
            "High risk",
        ]

        # 测试最小输入
        minimal_content = [
            {
                "type": "text",
                "text": "Participants were analyzed in their assigned groups.",
                "page_idx": 0,
            }
        ]
        minimal_result = agent.evaluate(minimal_content)
        rprint("\n[bold red]Minimal Input Test (Assignment):[/bold red]")
        print_llm_response(minimal_result)

        # 验证最小输入结果结构
        assert "domain" in minimal_result
        assert "signals" in minimal_result
        assert "overall" in minimal_result
        assert minimal_result["overall"]["risk"] in [
            "Low risk",
            "Some concerns",
            "High risk",
        ]

    except Exception as e:
        rprint(
            f"\n[bold red]Error during assignment error case testing:[/bold red] {str(e)}"
        )
        raise


def test_domain_deviation_adherence_error_cases():
    """测试Adherence子代理的错误情况"""
    agent = DomainDeviationAdherenceAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    try:
        # 测试空输入
        empty_result = agent.evaluate([])
        rprint("\n[bold red]Empty Input Test (Adherence):[/bold red]")
        print_llm_response(empty_result)

        # 验证空输入结果结构
        assert "domain" in empty_result
        assert "signals" in empty_result
        assert "overall" in empty_result
        assert "q2_7" not in empty_result["signals"]  # adherence类型不应该有q2_7
        assert empty_result["overall"]["risk"] in [
            "Low risk",
            "Some concerns",
            "High risk",
        ]

        # 测试最小输入
        minimal_content = [
            {
                "type": "text",
                "text": "The trial had good adherence to the intervention protocol.",
                "page_idx": 0,
            }
        ]
        minimal_result = agent.evaluate(minimal_content)
        rprint("\n[bold red]Minimal Input Test (Adherence):[/bold red]")
        print_llm_response(minimal_result)

        # 验证最小输入结果结构
        assert "domain" in minimal_result
        assert "signals" in minimal_result
        assert "overall" in minimal_result
        assert minimal_result["overall"]["risk"] in [
            "Low risk",
            "Some concerns",
            "High risk",
        ]

    except Exception as e:
        rprint(
            f"\n[bold red]Error during adherence error case testing:[/bold red] {str(e)}"
        )
        raise


if __name__ == "__main__":
    pytest.main(["-v", __file__])
