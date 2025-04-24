from typing import List, Dict, Any


class Rob2EvaluationResult:
    def __init__(self, summary: str, details: List[Dict[str, Any]]):
        self.summary = summary
        self.details = details

    def __repr__(self):
        return f"<Rob2EvaluationResult summary={self.summary} details={self.details}>"

    def to_dict(self):
        return {"summary": self.summary, "details": self.details}
