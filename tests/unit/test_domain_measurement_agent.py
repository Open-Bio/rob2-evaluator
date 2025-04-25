import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_measurement import DomainMeasurementAgent
from rob2_evaluator.agents.domain_agent import (
    SignalJudgement,
    DomainJudgement,
    GenericDomainJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(signal_answer="Y", domain_risk="Low risk"):
    signals = {}
    for q_id in ["q4_1", "q4_2", "q4_3", "q4_4", "q4_5"]:
        signals[q_id] = SignalJudgement(
            answer=signal_answer,
            reason="充分理由说明该答案",
            evidence=[{"page_idx": 0, "text": "measurement appropriate"}],
        )

    return GenericDomainJudgement(
        signals=signals,
        overall=DomainJudgement(
            risk=domain_risk,
            reason="领域评分理由",
            evidence=[{"page_idx": 0, "text": "measurement appropriate"}],
        ),
    )


def test_evaluate_measurement_all_yes_low_risk(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",  # 修正 patch 路径
        return_value=mock_judgement("Y", "Low risk"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Measurement of the outcome"
        for q in ["q4_1", "q4_2", "q4_3", "q4_4", "q4_5"]:
            assert result["signals"][q]["answer"] == "Y"
            assert isinstance(result["signals"][q]["reason"], str)
            assert isinstance(result["signals"][q]["evidence"], list)
        assert result["overall"]["risk"] == "Low risk"
        assert isinstance(result["overall"]["reason"], str)
        assert isinstance(result["overall"]["evidence"], list)


def test_evaluate_measurement_all_no_high_risk(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",  # 修正 patch 路径
        return_value=mock_judgement("N", "High risk"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q4_1", "q4_2", "q4_3", "q4_4", "q4_5"]:
            assert result["signals"][q]["answer"] == "N"
        assert result["overall"]["risk"] == "High risk"


def test_evaluate_measurement_some_concerns(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",  # 修正 patch 路径
        return_value=mock_judgement("NI", "Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q4_1", "q4_2", "q4_3", "q4_4", "q4_5"]:
            assert result["signals"][q]["answer"] == "NI"
        assert result["overall"]["risk"] == "Some concerns"


def test_evaluate_measurement_error_handling(sample_content):
    agent = DomainMeasurementAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",  # 修正 patch 路径
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
