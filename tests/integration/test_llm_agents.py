import pytest
from rob2_evaluator.agents.domain_randomization import DomainRandomizationAgent
from tests.fixtures.sample_content import sample_content
from rob2_evaluator.llm.models import ModelProvider


def test_domain_randomization_with_ollama(sample_content):
    """测试 DomainRandomizationAgent 与 Ollama 的实际交互"""

    agent = DomainRandomizationAgent(
        model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA
    )

    result = agent.evaluate(sample_content)

    # 验证返回的结构
    assert "domain" in result
    assert result["domain"] == "Randomization process"

    assert "judgement" in result
    judgement = result["judgement"]
    assert "q1_1" in judgement  # 随机序列
    assert "q1_2" in judgement  # 分配隐藏
    assert "q1_3" in judgement  # 基线差异
    assert "overall" in judgement

    # 验证判断结果的有效性
    valid_judgements = {"Low", "High", "Some concerns"}
    assert judgement["q1_1"] in valid_judgements
    assert judgement["q1_2"] in valid_judgements
    assert judgement["q1_3"] in valid_judgements
    assert judgement["overall"] in valid_judgements

    # 验证推理过程
    assert "reasoning" in result
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 0

    # 验证证据
    assert "evidence" in result
    assert isinstance(result["evidence"], list)
    for evidence in result["evidence"]:
        assert "page_idx" in evidence
        assert "text" in evidence
        assert isinstance(evidence["text"], str)
