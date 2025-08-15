"""
单Domain审查代理模块

为每个特定domain提供专门的审查器，确保上下文最小化
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from rob2_evaluator.config.model_config import ModelConfig
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.schema.rob2_schema import GenericDomainJudgement, DomainKey


class ReviewResult(BaseModel):
    """审查结果模型"""
    needs_revision: bool = Field(description="是否需要修改原始输出")
    revision_reasons: list[str] = Field(description="需要修改的原因列表", default_factory=list)
    revised_output: Optional[GenericDomainJudgement] = Field(description="修改后的输出内容", default=None)
    confidence: float = Field(description="审查结果的置信度(0-1)", ge=0, le=1)


class SingleDomainReviewer:
    """单Domain专用审查器，只关注特定domain的审查标准"""
    
    def __init__(
        self,
        domain_key: str,
        domain_standard: str,
        common_standard: str = "",
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ):
        """
        初始化单Domain审查器
        
        Args:
            domain_key: 要审查的domain标识
            domain_standard: 该domain的专项审查标准
            common_standard: 通用审查标准
            model_name: 模型名称
            model_provider: 模型提供商
        """
        self.domain_key = domain_key
        self.domain_standard = domain_standard
        self.common_standard = common_standard
        
        config = ModelConfig()
        self.model_name = model_name or config.get_model_name()
        self.model_provider = model_provider or config.get_model_provider()
    
    def review_and_revise(self, domain_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        审查并可能重写domain评估结果
        
        Args:
            domain_result: domain agent的原始评估结果
            
        Returns:
            经过审查和可能修改的评估结果
        """
        review_prompt = self._build_focused_prompt(domain_result)
        
        try:
            review_result: ReviewResult = call_llm(
                prompt=review_prompt,
                model_name=self.model_name,
                model_provider=self.model_provider,
                pydantic_model=ReviewResult,
                domain_key=f"review_{self.domain_key}",
            )
            
            final_result = domain_result.copy()
            
            # 如果需要修改，使用修改后的输出
            if review_result.needs_revision and review_result.revised_output:
                print(f"域 {self.domain_key} 的结果被修改: {review_result.revision_reasons}")
                
                # 将修改后的Pydantic模型转换为字典格式
                revised_data = self._convert_pydantic_to_dict(review_result.revised_output)
                
                # 更新signals和overall部分
                final_result['signals'] = revised_data['signals']
                final_result['overall'] = revised_data['overall']
                
                # 添加审查信息
                final_result['review_info'] = {
                    'was_revised': True,
                    'revision_reasons': review_result.revision_reasons,
                    'confidence': review_result.confidence,
                    'reviewed_at': self._get_timestamp(),
                    'reviewer_domain': self.domain_key
                }
            else:
                # 没有修改，但记录审查信息
                final_result['review_info'] = {
                    'was_revised': False,
                    'revision_reasons': [],
                    'confidence': review_result.confidence,
                    'reviewed_at': self._get_timestamp(),
                    'reviewer_domain': self.domain_key
                }
            
            return final_result
            
        except Exception as e:
            print(f"Review failed for {self.domain_key}: {e}")
            # 如果审查失败，返回原始结果并标记
            final_result = domain_result.copy()
            final_result['review_info'] = {
                'was_revised': False,
                'revision_reasons': [f"Review failed: {str(e)}"],
                'confidence': 0.0,
                'reviewed_at': self._get_timestamp(),
                'reviewer_domain': self.domain_key
            }
            return final_result
    
    def _build_focused_prompt(self, domain_result: Dict[str, Any]) -> str:
        """构建专注的审查prompt，只包含相关标准"""
        
        # 构建精简的标准描述
        standards_text = ""
        if self.domain_standard:
            standards_text += f"## {self.domain_key}专项标准：\n{self.domain_standard}\n\n"
        if self.common_standard:
            standards_text += f"## 通用要求：\n{self.common_standard}"
        
        prompt = f"""
你是{self.domain_key}的专项审查专家。请专门审查此domain的评估结果质量。

# 待审查的{self.domain_key}评估结果：
{domain_result}

# 审查标准：
{standards_text}

# 审查重点：
1. 检查signals评估是否符合{self.domain_key}的特定要求
2. 验证overall风险判断与signals的逻辑一致性
3. 确保证据充分支撑各项判断
4. 验证风险等级符合ROB2标准

# 输出要求：
- 如果结果符合标准：needs_revision = false
- 如果需要修改：needs_revision = true，并在revised_output中提供完整修正版本
- 在revision_reasons中说明具体修改原因
- revised_output必须是完整的GenericDomainJudgement格式

专注于{self.domain_key}的质量控制，确保评估符合ROB2框架要求。
"""
        return prompt
    
    def _convert_pydantic_to_dict(self, pydantic_model: GenericDomainJudgement) -> Dict[str, Any]:
        """将Pydantic模型转换为字典格式，匹配原有结构"""
        signals_dict = {}
        for signal_id, signal_data in pydantic_model.signals.items():
            evidence_list = []
            for ev in signal_data.evidence:
                evidence_list.append({
                    "text": ev.text,
                    "page_idx": ev.page_idx if ev.page_idx is not None else -1,
                })
            
            signals_dict[signal_id] = {
                "answer": signal_data.answer,
                "reason": signal_data.reason,
                "evidence": evidence_list,
            }
        
        overall_evidence = []
        for ev in pydantic_model.overall.evidence:
            overall_evidence.append({
                "text": ev.text,
                "page_idx": ev.page_idx if ev.page_idx is not None else -1,
            })
        
        return {
            "signals": signals_dict,
            "overall": {
                "risk": pydantic_model.overall.risk,
                "reason": pydantic_model.overall.reason,
                "evidence": overall_evidence,
            }
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


class DomainReviewerFactory:
    """Domain审查器工厂，为每个domain创建专门的审查器"""
    
    @staticmethod
    def create_reviewers(
        review_standards: Dict[str, str],
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ) -> Dict[str, SingleDomainReviewer]:
        """
        为每个domain创建专门的审查器
        
        Args:
            review_standards: 审查标准字典
            model_name: 模型名称
            model_provider: 模型提供商
            
        Returns:
            domain_key -> SingleDomainReviewer的映射
        """
        reviewers = {}
        common_standard = review_standards.get('default', '')
        
        # 为每个domain创建专门的审查器
        domain_keys = [
            DomainKey.RANDOMIZATION,
            DomainKey.DEVIATION_ASSIGNMENT, 
            DomainKey.DEVIATION_ADHERENCE,
            DomainKey.MISSING_DATA,
            DomainKey.MEASUREMENT,
            DomainKey.SELECTION
        ]
        for domain_key in domain_keys:
            domain_standard = review_standards.get(domain_key, '')
            if domain_standard:  # 只为有标准的domain创建审查器
                reviewers[domain_key] = SingleDomainReviewer(
                    domain_key=domain_key,
                    domain_standard=domain_standard,
                    common_standard=common_standard,
                    model_name=model_name,
                    model_provider=model_provider,
                )
        
        return reviewers