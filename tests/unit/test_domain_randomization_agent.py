import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_randomization import (
    DomainRandomizationAgent,
    RandomizationJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(risk_level="Low"):
    return RandomizationJudgement(
        q1_1=risk_level,
        q1_2=risk_level,
        q1_3=risk_level,
        overall=risk_level,
        reasoning="Randomization process was appropriate.",
        evidence=[{"page_idx": 0, "text": "randomized to treatment groups"}],
    )


def test_evaluate_randomization_low_risk(sample_content):
    agent = DomainRandomizationAgent()
    with patch(
        "rob2_evaluator.agents.domain_randomization.call_llm",
        return_value=mock_judgement("Low"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Randomization process"
        assert result["judgement"]["q1_1"] == "Low"
        assert result["judgement"]["q1_2"] == "Low"
        assert result["judgement"]["q1_3"] == "Low"
        assert result["judgement"]["overall"] == "Low"
        assert isinstance(result["evidence"], list)
        assert result["reasoning"] == "Randomization process was appropriate."


def test_evaluate_randomization_high_risk(sample_content):
    agent = DomainRandomizationAgent()
    with patch(
        "rob2_evaluator.agents.domain_randomization.call_llm",
        return_value=mock_judgement("High"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "High"
        assert all(
            v == "High" for k, v in result["judgement"].items() if k != "reasoning"
        )


def test_evaluate_randomization_some_concerns(sample_content):
    agent = DomainRandomizationAgent()
    with patch(
        "rob2_evaluator.agents.domain_randomization.call_llm",
        return_value=mock_judgement("Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "Some concerns"


def test_evaluate_randomization_empty_items(sample_content):
    agent = DomainRandomizationAgent()
    with patch(
        "rob2_evaluator.agents.domain_randomization.call_llm",
        return_value=mock_judgement("High"),
    ):
        result = agent.evaluate([])
        assert result["domain"] == "Randomization process"
        assert "judgement" in result
        assert "evidence" in result


def test_evaluate_randomization_error_handling(sample_content):
    agent = DomainRandomizationAgent()
    with patch(
        "rob2_evaluator.agents.domain_randomization.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
