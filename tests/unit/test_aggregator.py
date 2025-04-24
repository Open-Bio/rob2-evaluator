from rob2_evaluator.agents.aggregator import Aggregator


def test_aggregator_high():
    domain_results = [
        {"domain": "Domain 1", "judgement": {"overall": "Low"}},
        {"domain": "Domain 2", "judgement": {"overall": "High"}},
    ]
    agg = Aggregator()
    result = agg.evaluate(domain_results)
    assert result["judgement"]["overall"] == "High"
    assert "Domain 2" in result["reasoning"]


def test_aggregator_low():
    domain_results = [
        {"domain": "Domain 1", "judgement": {"overall": "Low"}},
        {"domain": "Domain 2", "judgement": {"overall": "Low"}},
    ]
    agg = Aggregator()
    result = agg.evaluate(domain_results)
    assert result["judgement"]["overall"] == "Low"


def test_aggregator_some_concerns():
    domain_results = [
        {"domain": "Domain 1", "judgement": {"overall": "Low"}},
        {"domain": "Domain 2", "judgement": {"overall": "Some concerns"}},
    ]
    agg = Aggregator()
    result = agg.evaluate(domain_results)
    assert result["judgement"]["overall"] == "Some concerns"
