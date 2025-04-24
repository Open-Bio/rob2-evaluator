import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_measurement import (
    DomainMeasurementAgent,
    MeasurementJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(risk_level="Low"):
    return MeasurementJudgement(
        q4_1=risk_level,
        q4_2=risk_level,
        q4_3=risk_level,
        q4_4=risk_level,
        q4_5=risk_level,
        overall=risk_level,
        reasoning="Appropriate measurement methods.",
        evidence=[{"page_idx": 0, "text": "measurement appropriate"}],
    )


def test_evaluate_measurement_low_risk(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_measurement.call_llm",
        return_value=mock_judgement("Low"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Measurement of the outcome"
        assert result["judgement"]["q4_1"] == "Low"
        assert result["judgement"]["q4_2"] == "Low"
        assert result["judgement"]["q4_3"] == "Low"
        assert result["judgement"]["q4_4"] == "Low"
        assert result["judgement"]["q4_5"] == "Low"
        assert result["judgement"]["overall"] == "Low"
        assert isinstance(result["evidence"], list)
        assert result["reasoning"] == "Appropriate measurement methods."


def test_evaluate_measurement_high_risk(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_measurement.call_llm",
        return_value=mock_judgement("High"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "High"
        assert all(
            v == "High" for k, v in result["judgement"].items() if k != "reasoning"
        )


def test_evaluate_measurement_some_concerns(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_measurement.call_llm",
        return_value=mock_judgement("Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        assert result["judgement"]["overall"] == "Some concerns"


def test_evaluate_measurement_error_handling(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_measurement.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
