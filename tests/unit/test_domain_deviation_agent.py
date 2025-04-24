import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_deviation import (
    DomainDeviationAgent,
    DeviationJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(risk_level="Low", analysis_type="assignment"):
    return DeviationJudgement(
        analysis_type=analysis_type,
        q2_1=risk_level,
        q2_2=risk_level,
        q2_3=risk_level,
        q2_4=risk_level,
        q2_5=risk_level,
        q2_6=risk_level,
        q2_7=risk_level if analysis_type == "assignment" else None,
        overall=risk_level,
        reasoning="Study protocol was followed with no significant deviations from intended interventions.",
        evidence=[{"page_idx": 0, "text": "followed protocol as intended"}],
    )


def test_evaluate_deviation_assignment_low_risk(sample_content):
    agent = DomainDeviationAgent()
    with patch(
        "rob2_evaluator.agents.domain_deviation.call_llm",
        return_value=mock_judgement("Low", "assignment"),
    ):
        result = agent.evaluate(sample_content, analysis_type="assignment")
        assert result["domain"] == "Deviations from intended interventions"
        assert result["judgement"]["analysis_type"] == "assignment"
        assert result["judgement"]["q2_1"] == "Low"
        assert result["judgement"]["q2_7"] == "Low"
        assert result["judgement"]["overall"] == "Low"
        assert isinstance(result["evidence"], list)
        assert "protocol" in result["reasoning"].lower()


def test_evaluate_deviation_adherence_low_risk(sample_content):
    agent = DomainDeviationAgent()
    with patch(
        "rob2_evaluator.agents.domain_deviation.call_llm",
        return_value=mock_judgement("Low", "adherence"),
    ):
        result = agent.evaluate(sample_content, analysis_type="adherence")
        assert result["judgement"]["analysis_type"] == "adherence"
        assert "q2_7" not in result["judgement"]
        assert result["judgement"]["overall"] == "Low"


def test_evaluate_deviation_assignment_high_risk(sample_content):
    agent = DomainDeviationAgent()
    with patch(
        "rob2_evaluator.agents.domain_deviation.call_llm",
        return_value=mock_judgement("High", "assignment"),
    ):
        result = agent.evaluate(sample_content, analysis_type="assignment")
        assert result["judgement"]["overall"] == "High"
        # Check all judgements except reasoning and analysis_type are High
        assert all(
            v == "High"
            for k, v in result["judgement"].items()
            if k not in ["reasoning", "analysis_type"]
        )


def test_evaluate_deviation_some_concerns(sample_content):
    agent = DomainDeviationAgent()
    with patch(
        "rob2_evaluator.agents.domain_deviation.call_llm",
        return_value=mock_judgement("Some concerns", "assignment"),
    ):
        result = agent.evaluate(sample_content, analysis_type="assignment")
        assert result["judgement"]["overall"] == "Some concerns"


def test_evaluate_deviation_invalid_type(sample_content):
    agent = DomainDeviationAgent()
    with pytest.raises(ValueError) as exc_info:
        agent.evaluate(sample_content, analysis_type="invalid")
    assert "analysis_type must be either 'assignment' or 'adherence'" in str(
        exc_info.value
    )


def test_evaluate_deviation_error_handling(sample_content):
    agent = DomainDeviationAgent()
    with patch(
        "rob2_evaluator.agents.domain_deviation.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content, analysis_type="assignment")
        assert "LLM Error" in str(exc_info.value)
