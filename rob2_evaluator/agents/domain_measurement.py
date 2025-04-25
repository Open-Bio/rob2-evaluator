from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.agents.domain_agent import DomainAgent
from pydantic import BaseModel
from typing import List, Dict, Any
from rob2_evaluator.schema.rob2_schema import DomainKey


# 子信号问题结构
class MeasurementSignalJudgement(BaseModel):
    answer: str  # Y, PY, PN, N, NI
    reason: str
    evidence: List[Dict[str, Any]]  # 每项含page_idx和text


# 领域评分结构
class MeasurementDomainJudgement(BaseModel):
    risk: str  # Low risk / Some concerns / High risk
    reason: str
    evidence: List[Dict[str, Any]]


class MeasurementJudgement(BaseModel):
    q4_1: MeasurementSignalJudgement
    q4_2: MeasurementSignalJudgement
    q4_3: MeasurementSignalJudgement
    q4_4: MeasurementSignalJudgement
    q4_5: MeasurementSignalJudgement
    overall: MeasurementDomainJudgement


class DomainMeasurementAgent(DomainAgent):
    def __init__(self, model_name="gemma3:27b", model_provider=ModelProvider.OLLAMA):
        super().__init__(DomainKey.MEASUREMENT, model_name, model_provider)
