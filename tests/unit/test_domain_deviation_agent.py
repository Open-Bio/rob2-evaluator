import pytest
from unittest.mock import patch
from rob2_evaluator.agents.domain_deviation import (
    DomainDeviationAssignmentAgent,
    DomainDeviationAdherenceAgent,
)
from rob2_evaluator.schema.rob2_schema import (
    SignalJudgement,
    DomainJudgement,
    GenericDomainJudgement,
)
from tests.fixtures.sample_content import sample_content


def mock_judgement(
    signal_answer="Y", domain_risk="Low risk", analysis_type="assignment"
):
    if analysis_type == "assignment":
        q_ids = ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6", "q2_7"]
    else:
        q_ids = ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6"]
    signals = {
        q: SignalJudgement(
            answer=signal_answer,
            reason="充分理由说明该答案",
            evidence=[{"page_idx": 0, "text": "followed protocol as intended"}],
        )
        for q in q_ids
    }
    return GenericDomainJudgement(
        signals=signals,
        overall=DomainJudgement(
            risk=domain_risk,
            reason="领域评分理由",
            evidence=[{"page_idx": 0, "text": "followed protocol as intended"}],
        ),
    )


def test_assignment_low_risk(sample_content):
    agent = DomainDeviationAssignmentAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("Y", "Low risk", "assignment"),
    ):
        result = agent.evaluate(sample_content)
        assert (
            result["domain"]
            == "Deviations from intended interventions (effect of assignment)"
        )
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6", "q2_7"]:
            assert result["signals"][q]["answer"] == "Y"
        assert result["overall"]["risk"] == "Low risk"


def test_assignment_high_risk(sample_content):
    agent = DomainDeviationAssignmentAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("N", "High risk", "assignment"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6", "q2_7"]:
            assert result["signals"][q]["answer"] == "N"
        assert result["overall"]["risk"] == "High risk"


def test_assignment_some_concerns(sample_content):
    agent = DomainDeviationAssignmentAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("NI", "Some concerns", "assignment"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6", "q2_7"]:
            assert result["signals"][q]["answer"] == "NI"
        assert result["overall"]["risk"] == "Some concerns"


def test_assignment_error_handling(sample_content):
    agent = DomainDeviationAssignmentAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)


def test_adherence_low_risk(sample_content):
    agent = DomainDeviationAdherenceAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("Y", "Low risk", "adherence"),
    ):
        result = agent.evaluate(sample_content)
        assert (
            result["domain"]
            == "Deviations from intended interventions (effect of adherence)"
        )
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6"]:
            assert result["signals"][q]["answer"] == "Y"
        assert "q2_7" not in result["signals"]
        assert result["overall"]["risk"] == "Low risk"


def test_adherence_high_risk(sample_content):
    agent = DomainDeviationAdherenceAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("N", "High risk", "adherence"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6"]:
            assert result["signals"][q]["answer"] == "N"
        assert result["overall"]["risk"] == "High risk"


def test_adherence_some_concerns(sample_content):
    agent = DomainDeviationAdherenceAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        return_value=mock_judgement("NI", "Some concerns", "adherence"),
    ):
        result = agent.evaluate(sample_content)
        for q in ["q2_1", "q2_2", "q2_3", "q2_4", "q2_5", "q2_6"]:
            assert result["signals"][q]["answer"] == "NI"
        assert result["overall"]["risk"] == "Some concerns"


def test_adherence_error_handling(sample_content):
    agent = DomainDeviationAdherenceAgent()
    with patch(
        "rob2_evaluator.agents.domain_agent.call_llm",
        side_effect=Exception("LLM Error"),
    ):
        with pytest.raises(Exception) as exc_info:
            agent.evaluate(sample_content)
        assert "LLM Error" in str(exc_info.value)
