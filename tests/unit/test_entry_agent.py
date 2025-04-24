import pytest
from unittest.mock import patch
from rob2_evaluator.agents.entry_agent import EntryAgent
from tests.fixtures.sample_content import sample_content


def test_filter_relevant_basic(sample_content):
    agent = EntryAgent(context_window=0)
    with patch.object(agent, "is_relevant_llm", side_effect=[False, True]):
        result = agent.filter_relevant(sample_content)
        assert len(result) == 1
        assert (
            "randomized" in result[0]["text"].lower()
            or "randomization" in result[0]["text"].lower()
        )


def test_filter_relevant_empty():
    agent = EntryAgent()
    with patch.object(agent, "is_relevant_llm", return_value=False):
        result = agent.filter_relevant([])
        assert result == []


def test_filter_relevant_all_irrelevant(sample_content):
    agent = EntryAgent()
    with patch.object(agent, "is_relevant_llm", return_value=False):
        result = agent.filter_relevant(sample_content)
        assert result == []
