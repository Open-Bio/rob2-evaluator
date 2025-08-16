"""
Single Domain Review Agent Module

Provides specialized reviewers for each specific domain, ensuring strict decision path compliance
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from rob2_evaluator.config.model_config import ModelConfig
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.schema.rob2_schema import GenericDomainJudgement, DomainKey


class ReviewResult(BaseModel):
    """Review result model with decision path tracking"""

    needs_revision: bool = Field(
        description="Whether the original output needs revision"
    )
    revision_reasons: list[str] = Field(
        description="List of reasons for revision", default_factory=list
    )
    revised_output: Optional[GenericDomainJudgement] = Field(
        description="Revised output content", default=None
    )
    confidence: float = Field(
        description="Confidence level of the review result (0-1)", ge=0, le=1
    )
    path: str = Field(
        description="The decision path taken, e.g., 'PATH_1: q1_1[Y] -> q1_3[N] -> Low risk'",
        default="",
    )


class SingleDomainReviewer:
    """Single Domain specialized reviewer focusing on decision path compliance"""

    def __init__(
        self,
        domain_key: str,
        domain_standard: str,
        common_standard: str = "",
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ):
        """
        Initialize Single Domain Reviewer

        Args:
            domain_key: Domain identifier to review
            domain_standard: Domain-specific decision path standards
            common_standard: Common review standards
            model_name: Model name
            model_provider: Model provider
        """
        self.domain_key = domain_key
        self.domain_standard = domain_standard
        self.common_standard = common_standard

        config = ModelConfig()
        self.model_name = model_name or config.get_model_name()
        self.model_provider = model_provider or config.get_model_provider()

    def review_and_revise(self, domain_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review and potentially revise domain evaluation results based on decision paths

        Args:
            domain_result: Original evaluation result from domain agent

        Returns:
            Reviewed and potentially revised evaluation result with decision path
        """
        review_prompt = self._build_path_review_prompt(domain_result)

        try:
            review_result: ReviewResult = call_llm(
                prompt=review_prompt,
                model_name=self.model_name,
                model_provider=self.model_provider,
                pydantic_model=ReviewResult,
                domain_key=f"review_{self.domain_key}",
            )

            final_result = domain_result.copy()

            # Always add the decision path information
            final_result["decision_path"] = review_result.path

            # If revision is needed, use the revised output
            if review_result.needs_revision and review_result.revised_output:
                print(f"Domain {self.domain_key} revised - Path: {review_result.path}")
                print(f"Reasons: {review_result.revision_reasons}")

                # Convert revised Pydantic model to dictionary format
                revised_data = self._convert_pydantic_to_dict(
                    review_result.revised_output
                )

                # Update signals and overall sections
                final_result["signals"] = revised_data["signals"]
                final_result["overall"] = revised_data["overall"]

                # Add review information with path
                final_result["review_info"] = {
                    "was_revised": True,
                    "decision_path": review_result.path,
                    "revision_reasons": review_result.revision_reasons,
                    "confidence": review_result.confidence,
                    "reviewed_at": self._get_timestamp(),
                    "reviewer_domain": self.domain_key,
                }
            else:
                # No revision needed, but record review information with path
                final_result["review_info"] = {
                    "was_revised": False,
                    "decision_path": review_result.path,
                    "revision_reasons": [],
                    "confidence": review_result.confidence,
                    "reviewed_at": self._get_timestamp(),
                    "reviewer_domain": self.domain_key,
                }

            return final_result

        except Exception as e:
            print(f"Review failed for {self.domain_key}: {e}")
            # If review fails, return original result with error marking
            final_result = domain_result.copy()
            final_result["decision_path"] = "REVIEW_FAILED"
            final_result["review_info"] = {
                "was_revised": False,
                "decision_path": "REVIEW_FAILED",
                "revision_reasons": [f"Review failed: {str(e)}"],
                "confidence": 0.0,
                "reviewed_at": self._get_timestamp(),
                "reviewer_domain": self.domain_key,
            }
            return final_result

    def _build_path_review_prompt(self, domain_result: Dict[str, Any]) -> str:
        """Build focused prompt for decision path review"""

        # Extract signal questions from the domain result
        signal_ids = list(domain_result.get("signals", {}).keys())

        prompt = f"""# ROB2 Decision Path Reviewer

You are a strict decision path auditor for the {self.domain_key} domain. Your ONLY task is to verify that the evaluation follows the exact decision path rules.

## Decision Path Rules - {self.domain_key}
{self.domain_standard}

## Common Requirements
{self.common_standard if self.common_standard else "None"}

## Evaluation Result to Review
```json
{self._format_json_for_prompt(domain_result)}
```

## Review Instructions

### Step 1: Identify the Path
Based on the signal answers, determine which PATH should be followed according to the decision rules above.

### Step 2: Verify Compliance
Check if the overall risk judgment matches the endpoint of the identified path.

### Step 3: Enforce Correction
If there is ANY mismatch between the path and the result:
- The decision path is the ONLY reference - no exceptions
- Either signal answers or overall risk MUST be revised to comply
- Prefer keeping signals with strong evidence, adjust overall risk
- If signals lack evidence, they can be adjusted to match a valid path

## Critical Rules
1. Decision paths are MANDATORY - no deviation allowed
2. Every signal combination MUST match exactly one path
3. The overall risk MUST equal the path's endpoint
4. When conflict exists, correction is NON-NEGOTIABLE

## Required Output Format

Return ONLY a JSON object with this exact structure:

### If path is followed correctly:
```json
{{
  "needs_revision": false,
  "path": "PATH_X: q1_1[Y] -> q1_3[N] -> Low risk",
  "revision_reasons": [],
  "revised_output": null,
  "confidence": 0.95
}}
```

### If revision is required:
```json
{{
  "needs_revision": true,
  "path": "PATH_X: [full path description]",
  "revision_reasons": [
    "Overall risk was 'Some concerns' but PATH_5 requires 'Low risk'",
    "Signal q1_3 answer conflicts with the decision path"
  ],
  "revised_output": {{
    "signals": {{
      {self._generate_signal_template(signal_ids)}
    }},
    "overall": {{
      "risk": "Low/Some concerns/High",
      "reason": "Summary explaining how signals lead to this risk per the path",
      "evidence": [
        {{
          "text": "Most relevant supporting quote",
          "page_idx": 1
        }}
      ]
    }}
  }},
  "confidence": 0.85
}}
```

## Important
- The `path` field MUST specify which PATH was identified (e.g., "PATH_1: q1_1[Y] -> q1_3[N] -> Low risk")
- Include ALL signals in revised_output, not just changed ones
- The revised output MUST comply with the identified path
- Return ONLY the JSON object, no additional text

Remember: The decision path is the ABSOLUTE authority. Any deviation must be corrected."""

        return prompt

    def _format_json_for_prompt(self, data: Dict[str, Any]) -> str:
        """Format JSON data for inclusion in prompt"""
        import json

        return json.dumps(data, indent=2, ensure_ascii=False)

    def _generate_signal_template(self, signal_ids: list) -> str:
        """Generate signal template for prompt"""
        if not signal_ids:
            return '"signal_id": { "answer": "Y/PY/PN/N/NI", "reason": "...", "evidence": [...] }'

        # Show first signal as example
        first_signal = signal_ids[0]
        template = f'"{first_signal}": {{ "answer": "Y/PY/PN/N/NI", "reason": "Detailed reasoning", "evidence": [{{ "text": "Quote", "page_idx": 1 }}] }}'

        if len(signal_ids) > 1:
            template += f",\n      // ... include all {len(signal_ids)} signals with same structure"

        return template

    def _convert_pydantic_to_dict(
        self, pydantic_model: GenericDomainJudgement
    ) -> Dict[str, Any]:
        """Convert Pydantic model to dictionary format matching original structure"""
        signals_dict = {}
        for signal_id, signal_data in pydantic_model.signals.items():
            evidence_list = []
            for ev in signal_data.evidence:
                evidence_list.append(
                    {
                        "text": ev.text,
                        "page_idx": ev.page_idx if ev.page_idx is not None else -1,
                    }
                )

            signals_dict[signal_id] = {
                "answer": signal_data.answer,
                "reason": signal_data.reason,
                "evidence": evidence_list,
            }

        overall_evidence = []
        for ev in pydantic_model.overall.evidence:
            overall_evidence.append(
                {
                    "text": ev.text,
                    "page_idx": ev.page_idx if ev.page_idx is not None else -1,
                }
            )

        return {
            "signals": signals_dict,
            "overall": {
                "risk": pydantic_model.overall.risk,
                "reason": pydantic_model.overall.reason,
                "evidence": overall_evidence,
            },
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()


class DomainReviewerFactory:
    """Domain reviewer factory, creates specialized reviewers for each domain"""

    @staticmethod
    def create_reviewers(
        review_standards: Dict[str, str],
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ) -> Dict[str, SingleDomainReviewer]:
        """
        Create specialized reviewers for each domain

        Args:
            review_standards: Dictionary of review standards with decision paths
            model_name: Model name
            model_provider: Model provider

        Returns:
            Mapping of domain_key -> SingleDomainReviewer
        """
        reviewers = {}
        common_standard = review_standards.get("default", "")

        # Create specialized reviewer for each domain
        domain_keys = [
            DomainKey.RANDOMIZATION,
            DomainKey.DEVIATION_ASSIGNMENT,
            DomainKey.DEVIATION_ADHERENCE,
            DomainKey.MISSING_DATA,
            DomainKey.MEASUREMENT,
            DomainKey.SELECTION,
        ]

        for domain_key in domain_keys:
            domain_standard = review_standards.get(domain_key, "")
            if domain_standard:  # Only create reviewers for domains with standards
                reviewers[domain_key] = SingleDomainReviewer(
                    domain_key=domain_key,
                    domain_standard=domain_standard,
                    common_standard=common_standard,
                    model_name=model_name,
                    model_provider=model_provider,
                )

        return reviewers
