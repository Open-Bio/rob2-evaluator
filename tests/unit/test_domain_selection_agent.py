import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_selection import DomainSelectionAgent
from rob2_evaluator.schema.rob2_schema import (
    SignalJudgement,
    DomainJudgement,
    GenericDomainJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(signal_answer="Y", domain_risk="Low risk"):
    q_ids = ["q5_1", "q5_2", "q5_3"]
    signals = {
        q: SignalJudgement(
            answer=signal_answer,
            reason="充分理由说明该答案",
            evidence=[{"page_idx": 0, "text": "pre-specified analysis"}],
        )
        for q in q_ids
    }
    return GenericDomainJudgement(
        signals=signals,
        overall=DomainJudgement(
            risk=domain_risk,
            reason="领域评分理由",
            evidence=[{"page_idx": 0, "text": "pre-specified analysis"}],
        ),
    )


def test_evaluate_selection_low_risk(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("Y", "Low risk"),
    ):
        result = agent.evaluate(sample_content)
        assert result["domain"] == "Risk of bias in selection of the reported result"
        for q in ["q5_1", "q5_2", "q5_3"]:
            assert result["signals"][q]["answer"] == "Y"
        assert result["overall"]["risk"] == "Low risk"


def test_evaluate_selection_high_risk(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("N", "High risk"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q5_1", "q5_2", "q5_3"]:
            assert result["signals"][q]["answer"] == "N"
        assert result["overall"]["risk"] == "High risk"


def test_evaluate_selection_some_concerns(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("NI", "Some concerns"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q5_1", "q5_2", "q5_3"]:
            assert result["signals"][q]["answer"] == "NI"
        assert result["overall"]["risk"] == "Some concerns"


def test_evaluate_selection_error_handling(sample_content):
    agent = DomainSelectionAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
