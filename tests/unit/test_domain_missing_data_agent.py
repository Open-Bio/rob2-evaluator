import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_missing_data import (
    DomainMissingDataAgent,
    MissingDataJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(risk_level="Low"):
    return MissingDataJudgement(
        q3_1=risk_level,
        q3_2=risk_level,
        q3_3=risk_level,
        q3_4=risk_level,
        overall=risk_level,
        reasoning="Complete outcome data available.",
        evidence=[{"page_idx": 0, "text": "no missing data"}],
    )


def test_evaluate_missing_data_low_risk(sample_content):
    agent = DomainMissingDataAgent()
    with patch(
        "rob2_evaluator.agents.domain_missing_data.call_llm",
        return_value=mock_judgement("Low"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Missing outcome data"
        assert result["judgement"]["q3_1"] == "Low"
        assert result["judgement"]["q3_2"] == "Low"
        assert result["judgement"]["q3_3"] == "Low"
        assert result["judgement"]["q3_4"] == "Low"
        assert result["judgement"]["overall"] == "Low"
        assert isinstance(result["evidence"], list)
        assert result["reasoning"] == "Complete outcome data available."


def test_evaluate_missing_data_high_risk(sample_content):
    agent = DomainMissingDataAgent()
    with patch(
        "rob2_evaluator.agents.domain_missing_data.call_llm",
        return_value=mock_judgement("High"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "High"
        assert all(
            v == "High" for k, v in result["judgement"].items() if k != "reasoning"
        )


def test_evaluate_missing_data_some_concerns(sample_content):
    agent = DomainMissingDataAgent()
    with patch(
        "rob2_evaluator.agents.domain_missing_data.call_llm",
        return_value=mock_judgement("Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "Some concerns"


def test_evaluate_missing_data_error_handling(sample_content):
    agent = DomainMissingDataAgent()
    with patch(
        "rob2_evaluator.agents.domain_missing_data.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
