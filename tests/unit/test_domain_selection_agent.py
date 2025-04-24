import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_selection import (
    DomainSelectionAgent,
    SelectionJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(risk_level="Low"):
    return SelectionJudgement(
        q5_1=risk_level,
        q5_2=risk_level,
        q5_3=risk_level,
        overall=risk_level,
        reasoning="Pre-specified analysis plan followed.",
        evidence=[{"page_idx": 0, "text": "pre-specified analysis"}],
    )


def test_evaluate_selection_low_risk(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_selection.call_llm",
        return_value=mock_judgement("Low"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Selection of the reported result"
        assert result["judgement"]["q5_1"] == "Low"
        assert result["judgement"]["q5_2"] == "Low"
        assert result["judgement"]["q5_3"] == "Low"
        assert result["judgement"]["overall"] == "Low"
        assert isinstance(result["evidence"], list)
        assert result["reasoning"] == "Pre-specified analysis plan followed."


def test_evaluate_selection_high_risk(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_selection.call_llm",
        return_value=mock_judgement("High"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "High"
        assert all(
            v == "High" for k, v in result["judgement"].items() if k != "reasoning"
        )


def test_evaluate_selection_some_concerns(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_selection.call_llm",
        return_value=mock_judgement("Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "Some concerns"


def test_evaluate_selection_error_handling(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_selection.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
