import pytest
from rich import print as rprint
from rob2_evaluator.agents.domain_randomization import DomainRandomizationAgent
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.utils.json_io import load_json
import json


def print_llm_response(result):
    """打印格式化的LLM响应"""
    rprint("\n[bold cyan]===== LLM Response Details =====[/bold cyan]")
    rprint(json.dumps(result, indent=2, ensure_ascii=False))
    rprint("[bold cyan]=============================[/bold cyan]\n")


def test_domain_randomization_integration():
    # 1. 加载真实RCT文章数据
    test_content = load_json("examples/20.Gottlie.json")

    # 2. 实例化代理
    agent = DomainRandomizationAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    # 3. 执行评估
    try:
        result = agent.evaluate(test_content)

        # 打印详细的LLM响应
        print_llm_response(result)

        # 4. 结构验证
        assert "domain" in result
        assert result["domain"] == "Risk of bias arising from the randomization process"
        assert "signals" in result
        assert "overall" in result

        # 5. 信号问题验证
        signals = result["signals"]
        for q_id in ["q1_1", "q1_2", "q1_3"]:
            assert q_id in signals
            assert "answer" in signals[q_id]
            assert signals[q_id]["answer"] in ["Y", "PY", "PN", "N", "NI"]
            assert "reason" in signals[q_id]
            assert isinstance(signals[q_id]["evidence"], list)

            # 打印每个信号问题的详细评估
            rprint(f"\n[bold green]Signal {q_id} Assessment:[/bold green]")
            rprint(f"Answer: {signals[q_id]['answer']}")
            rprint(f"Reason: {signals[q_id]['reason']}")
            rprint("Evidence:")
            for e in signals[q_id]["evidence"]:
                rprint(f"- Page {e['page_idx']}: {e['text']}")

        # 6. 整体判断验证
        assert result["overall"]["risk"] in ["Low risk", "Some concerns", "High risk"]
        rprint("\n[bold yellow]Overall Assessment:[/bold yellow]")
        rprint(f"Risk Level: {result['overall']['risk']}")
        rprint(f"Reasoning: {result['overall']['reason']}")
        rprint("Evidence:")
        for e in result["overall"]["evidence"]:
            rprint(f"- Page {e['page_idx']}: {e['text']}")

    except Exception as e:
        rprint(f"\n[bold red]Error during evaluation:[/bold red] {str(e)}")
        raise


def test_domain_randomization_error_cases():
    """测试错误处理"""
    agent = DomainRandomizationAgent(
        model_name="gemma3",
        model_provider=ModelProvider.OLLAMA,
    )

    try:
        # 测试空输入
        empty_result = agent.evaluate([])
        rprint("\n[bold red]Empty Input Test:[/bold red]")
        print_llm_response(empty_result)

        # 验证空输入结果结构
        assert "domain" in empty_result
        assert "signals" in empty_result
        assert "overall" in empty_result
        assert empty_result["overall"]["risk"] in [
            "Low risk",
            "Some concerns",
            "High risk",
        ]

        # 测试最小输入
        minimal_content = [
            {"type": "text", "text": "This is a minimal test case.", "page_idx": 0}
        ]
        minimal_result = agent.evaluate(minimal_content)
        rprint("\n[bold red]Minimal Input Test:[/bold red]")
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
        rprint(f"\n[bold red]Error during error case testing:[/bold red] {str(e)}")
        raise


if __name__ == "__main__":
    pytest.main(["-v", __file__])
