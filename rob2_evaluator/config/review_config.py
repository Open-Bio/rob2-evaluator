"""
ROB2 Evaluation Review Standards Configuration Module

This module provides configuration functionality for review standards,
allowing users to customize decision path checking standards for each domain.
"""

from typing import Dict, Optional
import json
from pathlib import Path
from rob2_evaluator.schema.rob2_schema import DomainKey


class ReviewConfig:
    """Review configuration management class for decision path validation"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize review configuration

        Args:
            config_path: Custom configuration file path, uses default if None
        """
        self.config_path = config_path
        self._standards = self._load_standards()

    def _load_standards(self) -> Dict[str, str]:
        """Load review standards"""
        if self.config_path and Path(self.config_path).exists():
            return self._load_from_file(self.config_path)
        else:
            return self._get_default_standards()

    def _load_from_file(self, file_path: str) -> Dict[str, str]:
        """Load review standards from file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return config_data.get(
                    "review_standards", self._get_default_standards()
                )
        except Exception as e:
            print(f"Failed to load config file {file_path}: {e}")
            return self._get_default_standards()

    def get_standards(self) -> Dict[str, str]:
        """Get review standards"""
        return self._standards.copy()

    def update_standard(self, domain_key: str, standard: str) -> None:
        """Update review standard for specific domain"""
        self._standards[domain_key] = standard

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to file"""
        config_data = {
            "review_standards": self._standards,
            "description": "ROB2 Evaluation Decision Path Review Standards",
            "version": "1.0",
            "note": "These standards define the mandatory decision paths for each domain",
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            print(f"Configuration saved to: {file_path}")
        except Exception as e:
            print(f"Failed to save config file: {e}")

    def _get_default_standards(self) -> Dict[str, str]:
        """Get default review standards with decision paths"""
        return {
            DomainKey.RANDOMIZATION: """
## Decision Paths for Randomization Domain

**PATH_1**: q1_1[Y/PY/NI] -> q1_3[N/PN/NI] -> Low risk
Description: Proper randomization with no baseline imbalance

**PATH_2**: q1_1[Y/PY/NI] -> q1_3[Y/PY] -> Some concerns
Description: Proper randomization but with baseline imbalance

**PATH_3**: q1_1[N/PN] -> High risk
Description: No or inadequate randomization

**PATH_4**: q1_2[Y/PY] -> Low risk
Description: Adequate allocation concealment

**PATH_5**: q1_2[NI] -> q1_3[N/PN/NI] -> Low risk
Description: No information on concealment but no baseline issues

**PATH_6**: q1_2[NI] -> q1_3[Y/PY] -> High risk
Description: No information on concealment with baseline imbalance

**PATH_7**: q1_2[N/PN] -> High risk
Description: Inadequate allocation concealment

## Decision Logic
1. First check q1_1 (randomization method)
2. If q1_1 is N/PN, result is High risk (PATH_3)
3. If q1_1 is Y/PY/NI, check q1_2 (allocation concealment)
4. Follow the appropriate path based on q1_2 and q1_3 values
""",
            DomainKey.DEVIATION_ASSIGNMENT: """
## Decision Paths for Deviations from Intended Interventions (Assignment)

**PATH_1**: (2.1 & 2.2)[All N/PN] -> Low risk
Description: No deviations from intended intervention

**PATH_2**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[N/PN] -> Low risk
Description: Deviations occurred but appropriately analyzed

**PATH_3**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[NI] -> 2.4[N/PN] -> Some concerns
Description: No info on analysis but deviations unlikely to affect outcome

**PATH_4**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[NI] -> 2.4[Y/PY] -> 2.5[N/PN/NI] -> Some concerns
Description: Deviations could affect outcome but balanced between groups

**PATH_5**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[NI] -> 2.4[Y/PY] -> 2.5[Y/PY] -> High risk
Description: Deviations likely affected outcome and imbalanced

**PATH_6**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[Y/PY] -> Some concerns
Description: Inappropriate analysis used

**PATH_7**: 2.6[N/PN/NI] -> Low risk
Description: No failure in implementing intervention

**PATH_8**: 2.6[Y/PY] -> 2.7[N/PN] -> Some concerns
Description: Implementation failure but unlikely to affect outcome

**PATH_9**: 2.6[Y/PY] -> 2.7[Y/PY/NI] -> High risk
Description: Implementation failure likely affected outcome
""",
            DomainKey.DEVIATION_ADHERENCE: """
## Decision Paths for Deviations from Intended Interventions (Adherence)

**PATH_1**: (2.1 & 2.2)[All N/PN] -> 2.4[All NA/N/PN] -> Low risk
Description: No deviations and appropriate analysis

**PATH_2**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[N/PN/NI] -> 2.6[Y/PY] -> Some concerns
Description: Deviations present but addressed in analysis

**PATH_3**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[N/PN/NI] -> 2.6[N/PN/NI] -> High risk
Description: Deviations not appropriately addressed

**PATH_4**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[NA/Y/PY] -> 2.5[Any Y/PY/NI] -> Some concerns
Description: Trial analyzed appropriately but deviations present

**PATH_5**: (2.1 & 2.2)[Any Y/PY/NI] -> 2.3[NA/Y/PY] -> 2.5[All NA/N/PN] -> Low risk
Description: Appropriate per-protocol analysis with no issues
""",
            DomainKey.MISSING_DATA: """
## Decision Paths for Missing Outcome Data

**PATH_1**: 3.1[Y/PY] -> Low risk
Description: Outcome data available for all or nearly all participants

**PATH_2**: 3.1[N/PN/NI] -> 3.2[Y/PY] -> Low risk
Description: Evidence that missingness did not bias result

**PATH_3**: 3.1[N/PN/NI] -> 3.2[N/PN] -> 3.3[N/PN] -> Some concerns
Description: Missingness could depend on value but unlikely

**PATH_4**: 3.1[N/PN/NI] -> 3.2[N/PN] -> 3.3[Y/PY/NI] -> 3.4[N/PN] -> Some concerns
Description: Missingness could depend on value but balanced/handled

**PATH_5**: 3.1[N/PN/NI] -> 3.2[N/PN] -> 3.3[Y/PY/NI] -> 3.4[Y/PY/NI] -> High risk
Description: Missingness likely depends on true value
""",
            DomainKey.MEASUREMENT: """
## Decision Paths for Measurement of the Outcome

**PATH_1**: 4.1[Y/PY] -> High risk
Description: Measurement method inappropriate

**PATH_2**: 4.1[N/PN/NI] -> 4.2[N/PN] -> 4.3[N/PN] -> Low risk
Description: Appropriate method, no differential measurement

**PATH_3**: 4.1[N/PN/NI] -> 4.2[N/PN] -> 4.3[Y/PY/NI] -> 4.4[N/PN] -> Low risk
Description: Assessors aware but outcome not influenced

**PATH_4**: 4.1[N/PN/NI] -> 4.2[N/PN] -> 4.3[Y/PY/NI] -> 4.4[Y/PY/NI] -> 4.5[N/PN] -> Some concerns
Description: Outcome could be influenced but unlikely

**PATH_5**: 4.1[N/PN/NI] -> 4.2[N/PN] -> 4.3[Y/PY/NI] -> 4.4[Y/PY/NI] -> 4.5[Y/PY/NI] -> High risk
Description: Outcome likely influenced by knowledge of intervention

**PATH_6**: 4.1[N/PN/NI] -> 4.2[NI] -> 4.3[N/PN] -> Some concerns
Description: No info on differential measurement but assessors blinded

**PATH_7**: 4.1[N/PN/NI] -> 4.2[NI] -> 4.3[Y/PY/NI] -> 4.4[N/PN] -> Some concerns
Description: No info on differential measurement, assessors aware

**PATH_8**: 4.1[N/PN/NI] -> 4.2[NI] -> 4.3[Y/PY/NI] -> 4.4[Y/PY/NI] -> 4.5[N/PN] -> Some concerns
Description: Uncertain differential measurement, possible influence

**PATH_9**: 4.1[N/PN/NI] -> 4.2[NI] -> 4.3[Y/PY/NI] -> 4.4[Y/PY/NI] -> 4.5[Y/PY/NI] -> High risk
Description: Uncertain differential measurement, likely influenced

**PATH_10**: 4.1[N/PN/NI] -> 4.2[Y/PY] -> High risk
Description: Differential measurement errors likely
""",
            DomainKey.SELECTION: """
## Decision Paths for Selection of the Reported Result

**PATH_1**: (5.2 & 5.3)[All N/PN] -> 5.1[Y/PY] -> Low risk
Description: Results analyzed according to pre-specified plan

**PATH_2**: (5.2 & 5.3)[All N/PN] -> 5.1[N/PN/NI] -> Some concerns
Description: No pre-specified plan but no evidence of selection

**PATH_3**: (5.2 & 5.3)[At least one NI & none Y/PY] -> Some concerns
Description: Some concerns about result selection

**PATH_4**: (5.2 & 5.3)[Any Y/PY] -> High risk
Description: Evidence of selective reporting
""",
            "default": """
## Core Decision Path Principles

### Mandatory Execution Rules
1. **Strict Path Following**: Must follow the exact decision tree paths without deviation
2. **Sequential Processing**: Answer questions in the exact order specified by the paths
3. **No Autonomous Judgments**: Cannot make risk judgments outside of the defined paths
4. **Path Endpoints Are Final**: The risk level MUST match the path's endpoint exactly

### Execution Standards
- ✅ Follow if-then logic strictly
- ✅ Process each signal according to path conditions
- ✅ Trace complete path from start to risk endpoint
- ❌ PROHIBITED: Direct risk judgment based on intuition
- ❌ PROHIBITED: Skipping intermediate path steps
- ❌ PROHIBITED: Creating new paths or exceptions

### Conflict Resolution
When signal answers conflict with overall risk:
1. Identify the correct path based on signal answers
2. If overall risk doesn't match path endpoint, it MUST be changed
3. If signals lack strong evidence, they may be adjusted to match a valid path
4. The decision path is ABSOLUTE - no compromises allowed

Remember: These are not guidelines but MANDATORY rules. The decision path determines the outcome, not clinical judgment.
""",
        }


def create_sample_config_file(file_path: str = "review_standards.json") -> None:
    """Create sample configuration file with decision paths"""
    config = ReviewConfig()
    config.save_to_file(file_path)
    print(f"Sample configuration file created: {file_path}")
    print("You can edit this file to customize decision path standards")


def load_custom_standards(file_path: str) -> Dict[str, str]:
    """Convenience function to load custom review standards"""
    config = ReviewConfig(file_path)
    return config.get_standards()


if __name__ == "__main__":
    # Create sample configuration file
    create_sample_config_file()
