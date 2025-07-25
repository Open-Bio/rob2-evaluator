from typing import List, Dict, Any, Type, TypeVar, Optional
from pydantic import BaseModel, Field
from enum import Enum


# === 统一的证据条目模型定义 ===
class EvidenceItem(BaseModel):
    text: str = Field(description="Excerpt from original text supporting the judgment.")
    page_idx: Optional[int] = Field(
        description="The page number where this evidence text was found in the input context.",
        default=None,
    )


# === 统一的领域信号与评判结构定义 ===
class SignalJudgement(BaseModel):
    answer: str
    reason: str
    evidence: List[EvidenceItem]


class DomainJudgement(BaseModel):
    risk: str
    reason: str
    evidence: List[EvidenceItem]


class GenericDomainJudgement(BaseModel):
    signals: Dict[str, SignalJudgement]
    overall: DomainJudgement


class DomainKey(str, Enum):
    RANDOMIZATION = "randomization"
    DEVIATION_ASSIGNMENT = "deviation_assignment"
    DEVIATION_ADHERENCE = "deviation_adherence"
    MISSING_DATA = "missing_data"
    MEASUREMENT = "measurement"
    SELECTION = "selection"
    # 如有其它领域，继续添加


class Rob2EvaluationResult:
    def __init__(self, summary: str, details: List[Dict[str, Any]]):
        self.summary = summary
        self.details = details

    def __repr__(self):
        return f"<Rob2EvaluationResult summary={self.summary} details={self.details}>"

    def to_dict(self):
        return {"summary": self.summary, "details": self.details}


T = TypeVar("T", bound=BaseModel)


class DefaultResponseFactory:
    """负责生成各个领域的默认响应"""

    @staticmethod
    def create_default_signals(domain_key: str) -> Dict[str, Dict]:
        """根据领域创建默认的信号问题响应"""
        schema = DOMAIN_SCHEMAS[domain_key]
        signals = {}

        # 处理deviation领域的特殊情况
        if domain_key == "deviation":
            signal_list = schema["paths"]["assignment"]  # 默认使用assignment
        else:
            signal_list = schema["signals"]

        for signal in signal_list:
            signals[signal["id"]] = {
                "answer": "NI",  # 默认使用"No Information"
                "reason": "No information available",
                "evidence": [],
            }
        return signals

    @staticmethod
    def create_default_overall() -> Dict[str, Any]:
        """创建默认的整体评估"""
        return {
            "risk": "Some concerns",  # 采用保守的默认评估
            "reason": "Insufficient information for assessment",
            "evidence": [],
        }

    @classmethod
    def create_response(cls, model_class: Type[T], domain_key: str) -> T:
        """创建完整的默认响应"""
        default_values = {}

        # 处理signals和overall字段
        if "signals" in model_class.model_fields:
            default_values["signals"] = cls.create_default_signals(domain_key)
        if "overall" in model_class.model_fields:
            default_values["overall"] = cls.create_default_overall()

        # 处理其他字段
        for field_name, field in model_class.model_fields.items():
            if field_name not in ["signals", "overall"]:
                if field.annotation is str:
                    default_values[field_name] = "Some concerns"
                elif field.annotation is float:
                    default_values[field_name] = 0.0
                elif field.annotation is int:
                    default_values[field_name] = 0
                elif field_name == "evidence":
                    default_values[field_name] = []
                elif field_name == "analysis_type":
                    default_values[field_name] = "assignment"
                elif (
                    hasattr(field.annotation, "__origin__")
                    and field.annotation.__origin__ is dict
                ):
                    default_values[field_name] = {}
                else:
                    if hasattr(field.annotation, "__args__"):
                        default_values[field_name] = field.annotation.__args__[0]
                    else:
                        default_values[field_name] = None

        return model_class(**default_values)


# ROB2 各领域信号问题 schema 集中管理
DOMAIN_SCHEMAS = {
    "randomization": {
        "signals": [
            {
                "id": "q1_1",
                "text": "Was the allocation sequence random?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q1_2",
                "text": "Was the allocation sequence concealed until participants were enrolled and assigned to interventions?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q1_3",
                "text": "Did baseline differences between intervention groups suggest a problem with the randomization process?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias arising from the randomization process",
    },
    "deviation_assignment": {
        "signals": [
            {
                "id": "q2_1",
                "text": "Were participants aware of their assigned intervention during the trial?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_2",
                "text": "Were carers and people delivering the interventions aware of participants' assigned intervention during the trial?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_3",
                "text": "If Y/PY/NI to 2.1 or 2.2: Were there deviations from the intended intervention that arose because of the trial context?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_4",
                "text": "If Y/PY to 2.3: Were these deviations likely to have affected the outcome?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_5",
                "text": "If Y/PY/NI to 2.4: Were these deviations from intended intervention balanced between groups?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_6",
                "text": "Was an appropriate analysis used to estimate the effect of assignment to intervention?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_7",
                "text": "If N/PN/NI to 2.6: Was there potential for a substantial impact (on the result) of the failure to analyse participants in the group to which they were randomized?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias due to deviations from the intended interventions (effect of assignment)",
    },
    "deviation_adherence": {
        "signals": [
            {
                "id": "q2_1",
                "text": "Were participants aware of their assigned intervention during the trial?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_2",
                "text": "Were carers and people delivering the interventions aware of participants' assigned intervention during the trial?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_3",
                "text": "If Y/PY/NI to 2.1 or 2.2: Were important non-protocol interventions balanced across intervention groups?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_4",
                "text": "Were there failures in implementing the intervention that could have affected the outcome?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_5",
                "text": "Was there non-adherence to the assigned intervention regimen that could have affected participants’ outcomes?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q2_6",
                "text": "If N/PN/NI to 2.3, or Y/PY/NI to 2.4 or 2.5: Was an appropriate analysis used to estimate the effect of adhering to the intervention?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias due to deviations from the intended interventions (effect of adherence)",
    },
    "missing_data": {
        "signals": [
            {
                "id": "q3_1",
                "text": "Were data for this outcome available for all, or nearly all, participants randomized?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q3_2",
                "text": "If N/PN/NI to 3.1: Is there evidence that the result was not biased by missing outcome data?",
                "options": ["NA", "Y", "PY", "PN", "N"],
            },
            {
                "id": "q3_3",
                "text": "If N/PN to 3.2: Could missingness in the outcome depend on its true value?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q3_4",
                "text": "If Y/PY/NI to 3.3: Is it likely that missingness in the outcome depended on its true value?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias due to missing outcome data",
    },
    "measurement": {
        "signals": [
            {
                "id": "q4_1",
                "text": "Was the method of measuring the outcome inappropriate?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q4_2",
                "text": "Could measurement or ascertainment of the outcome have differed between intervention groups?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q4_3",
                "text": "If N/PN/NI to 4.1 and 4.2: Were outcome assessors aware of the intervention received by study participants?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q4_4",
                "text": "If Y/PY/NI to 4.3: Could assessment of the outcome have been influenced by knowledge of intervention received?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q4_5",
                "text": "If Y/PY/NI to 4.4: Is it likely that assessment of the outcome was influenced by knowledge of intervention received?",
                "options": ["NA", "Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias in measurement of the outcome",
    },
    "selection": {
        "signals": [
            {
                "id": "q5_1",
                "text": "Were the data that produced this result analysed in accordance with a pre-specified analysis plan that was finalized before unblinded outcome data were available for analysis?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q5_2",
                "text": "Was the result selected from multiple eligible outcome measurements (e.g. scales, definitions, time points) within the outcome domain?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
            {
                "id": "q5_3",
                "text": "Was the result selected from multiple eligible analyses of the data?",
                "options": ["Y", "PY", "PN", "N", "NI"],
            },
        ],
        "domain_options": ["Low risk", "Some concerns", "High risk"],
        "domain_name": "Risk of bias in selection of the reported result",
    },
}
