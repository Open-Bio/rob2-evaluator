import pytest
from unittest.mock import patch
from rob2_evaluator.agents.analysis_type_agent import AnalysisTypeAgent
from tests.fixtures.sample_content import sample_content


def test_infer_analysis_type_assignment(sample_content):
    agent = AnalysisTypeAgent()
    with patch(
        "rob2_evaluator.agents.analysis_type_agent.call_llm", return_value="assignment"
    ):
        result = agent.infer_analysis_type(sample_content)
        assert result == "assignment"


def test_infer_analysis_type_adherence(sample_content):
    agent = AnalysisTypeAgent()
    with patch(
        "rob2_evaluator.agents.analysis_type_agent.call_llm", return_value="adherence"
    ):
        result = agent.infer_analysis_type(sample_content)
        assert result == "adherence"


def test_infer_analysis_type_default_assignment(sample_content):
    agent = AnalysisTypeAgent()
    with patch(
        "rob2_evaluator.agents.analysis_type_agent.call_llm", return_value="unknown"
    ):
        result = agent.infer_analysis_type(sample_content)
        assert result == "assignment"
