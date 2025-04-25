from rob2_evaluator.schema.rob2_schema import (
    DOMAIN_SCHEMAS,
    GenericDomainJudgement,
)
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any, Optional
import re
from difflib import SequenceMatcher
from jinja2 import Template


class DomainAgent:
    def __init__(
        self,
        domain_key: str,
        model_name="gemma3:27b",
        model_provider=ModelProvider.OLLAMA,
        fuzzy_match_threshold: float = 0.8,
    ):
        self.domain_key = domain_key
        self.schema = DOMAIN_SCHEMAS[domain_key]
        self.model_name = model_name
        self.model_provider = model_provider
        self.fuzzy_match_threshold = fuzzy_match_threshold

    def _find_evidence_source(
        self, evidence_text: str, items: List[Dict[str, Any]]
    ) -> Dict:
        """Find the page index of the evidence text using fuzzy matching to improve accuracy"""
        # 1. Try exact match
        for item in items:
            item_text = item.get("text", "")
            if evidence_text.lower() in item_text.lower():
                # Found paragraph, locate the exact position to extract more accurate context
                start_pos = item_text.lower().find(evidence_text.lower())
                extract = item_text[
                    max(0, start_pos - 20) : min(
                        len(item_text), start_pos + len(evidence_text) + 20
                    )
                ]
                return {"text": extract, "page_idx": item.get("page_idx", -1)}

        # 2. If exact match fails, try fuzzy match
        best_match = None
        best_score = 0

        for item in items:
            item_text = item.get("text", "")
            # Use SequenceMatcher for fuzzy matching
            matcher = SequenceMatcher(None, evidence_text.lower(), item_text.lower())
            match = matcher.find_longest_match(0, len(evidence_text), 0, len(item_text))
            score = match.size / len(evidence_text) if evidence_text else 0

            if score > best_score and score >= self.fuzzy_match_threshold:
                best_score = score
                matched_text = item_text[match.b : (match.b + match.size)]
                # Extract context
                start_pos = max(0, match.b - 20)
                end_pos = min(len(item_text), match.b + match.size + 20)
                context = item_text[start_pos:end_pos]
                best_match = {
                    "text": context,
                    "page_idx": item.get("page_idx", -1),
                    "match_score": score,
                }

        return best_match if best_match else {"text": evidence_text, "page_idx": -1}

    def evaluate(self, items: List[Dict[str, Any]]):
        signals_schema = self.schema["signals"]
        prompt = self._build_prompt(items, signals_schema)
        result = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=GenericDomainJudgement,
            domain_key=self.domain_key,
        )

        # Process the evidence for each signal
        processed_signals = {}
        for signal_id, signal in result.signals.items():
            processed_evidence = [
                self._find_evidence_source(e.get("text", ""), items)
                for e in signal.evidence
            ]
            processed_signals[signal_id] = {
                "answer": signal.answer,
                "reason": signal.reason,
                "evidence": processed_evidence,
            }

        # Process the evidence for overall assessment
        processed_overall_evidence = [
            self._find_evidence_source(e.get("text", ""), items)
            for e in result.overall.evidence
        ]

        return {
            "domain": self.schema["domain_name"],
            "signals": processed_signals,
            "overall": {
                "risk": result.overall.risk,
                "reason": result.overall.reason,
                "evidence": processed_overall_evidence,
            },
        }

    def _build_prompt(
        self, items: List[Dict[str, Any]], signals_schema: List[Dict[str, Any]]
    ) -> str:
        """使用 Jinja2 模板构建 prompt，避免引号和格式问题"""
        context = "\n".join(
            [
                f"[Page {item.get('page_idx', '?')}] {item.get('text', '')}"
                for item in items
            ]
        )
        signal_options = signals_schema[0]["options"]
        domain_options = self.schema["domain_options"]
        domain_title = self.schema["domain_name"]

        # Jinja2 模板字符串
        prompt_template = """
# ROB2 Domain Evaluation Expert

## Task Background
You are an expert in the ROB2 framework, specializing in assessing risk of bias in randomized controlled trials (RCTs). You need to analyze the following study content and evaluate the risk of bias in the domain of "{{ domain_title }}".

## Evaluation Materials
The following content was extracted from the study (with page numbers):

{{ context }}

## Analysis Steps
1. Carefully read the above material
2. Answer each signal question one by one
3. Provide an overall domain-level risk assessment
4. Evidence must be directly quoted from the original text without modification.

## Signal Questions
{% for s in signals_schema -%}
{{ s.id }}: {{ s.text }}
{% endfor %}

Each question must be answered by selecting one of the following options: {{ signal_options | join('/') }}

## Overall Risk Assessment
Domain-level risk of bias judgment:
{% for opt in domain_options -%}
- {{ opt }}
{% endfor %}

## Output Format
Please return a JSON object in the following structure:

```json
{
  "signals": {
    {% for s in signals_schema -%}
    "{{ s.id }}": {
      "answer": "<Select: {{ signal_options | join('/') }}>",
      "reason": "<Detailed explanation>",
      "evidence": [
        {"text": "<Excerpt from original text>"}
      ]
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  },
  "overall": {
    "risk": "<Select: {{ domain_options | join('/') }}>",
    "reason": "<Detailed explanation of the overall judgment>",
    "evidence": [
      {"text": "<Excerpt from original text supporting the overall judgment>"}
    ]
  }
}
```
"""
        template = Template(prompt_template)
        prompt = template.render(
            context=context,
            signals_schema=signals_schema,
            signal_options=signal_options,
            domain_options=domain_options,
            domain_title=domain_title,
        )
        return prompt
