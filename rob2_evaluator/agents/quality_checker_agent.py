from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from rob2_evaluator.config.model_config import ModelConfig
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from rob2_evaluator.schema.rob2_schema import GenericDomainJudgement


class ReviewResult(BaseModel):
    """审查结果模型"""
    needs_revision: bool = Field(description="是否需要修改原始输出")
    revision_reasons: List[str] = Field(description="需要修改的原因列表", default_factory=list)
    revised_output: Optional[GenericDomainJudgement] = Field(description="修改后的输出内容", default=None)
    confidence: float = Field(description="审查结果的置信度(0-1)", ge=0, le=1)


class DomainReviewerAgent:
    """Domain结果审查代理，用于检查并重写domain agent的输出内容"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
        review_standards: Optional[Dict[str, str]] = None,
    ):
        config = ModelConfig()
        self.model_name = model_name or config.get_model_name()
        self.model_provider = model_provider or config.get_model_provider()
        
        # 审查标准配置，可以从外部传入或使用默认标准
        self.review_standards = review_standards or self._get_default_standards()
    
    def review_and_revise(self, domain_result: Dict[str, Any], domain_key: str) -> Dict[str, Any]:
        """
        检查并重写domain agent的评估结果
        
        Args:
            domain_result: domain agent的原始评估结果
            domain_key: domain的标识(如'domain_1', 'domain_2'等)
            
        Returns:
            经过审查和可能修改的评估结果
        """
        review_prompt = self._build_review_prompt(domain_result, domain_key)
        
        try:
            review_result: ReviewResult = call_llm(
                prompt=review_prompt,
                model_name=self.model_name,
                model_provider=self.model_provider,
                pydantic_model=ReviewResult,
                domain_key=f"review_{domain_key}",
            )
            
            final_result = domain_result.copy()
            
            # 如果需要修改，使用修改后的输出
            if review_result.needs_revision and review_result.revised_output:
                print(f"域 {domain_key} 的结果被修改: {review_result.revision_reasons}")
                
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
                    'reviewed_at': self._get_timestamp()
                }
            else:
                # 没有修改，但记录审查信息
                final_result['review_info'] = {
                    'was_revised': False,
                    'revision_reasons': [],
                    'confidence': review_result.confidence,
                    'reviewed_at': self._get_timestamp()
                }
            
            return final_result
            
        except Exception as e:
            print(f"Review failed for {domain_key}: {e}")
            # 如果审查失败，返回原始结果并标记
            final_result = domain_result.copy()
            final_result['review_info'] = {
                'was_revised': False,
                'revision_reasons': [f"Review failed: {str(e)}"],
                'confidence': 0.0,
                'reviewed_at': self._get_timestamp()
            }
            return final_result
    
    def _build_review_prompt(self, domain_result: Dict[str, Any], domain_key: str) -> str:
        """构建审查和重写的prompt"""
        
        # 获取该domain的具体审查标准和通用标准
        domain_standard = self.review_standards.get(domain_key, '')
        default_standard = self.review_standards.get('default', '')
        
        # 只包含当前domain相关的标准
        relevant_standards = ""
        if domain_standard:
            relevant_standards += f"## 专项标准 ({domain_key})：\n{domain_standard}\n\n"
        if default_standard:
            relevant_standards += f"## 通用标准：\n{default_standard}"
        
        prompt = f"""
你是一个专业的ROB2评估审查专家。请根据以下检查标准，审查{domain_key}的输出结果，如有必要请重写输出内容。

# 待审查的评估结果：
{domain_result}

# 适用的审查标准：
{relevant_standards}

# 审查要求：
1. **严格按照审查标准**：检查输出是否符合ROB2框架要求
2. **逻辑一致性**：signals评估与overall判断必须逻辑一致
3. **证据充分性**：每个判断必须有充分的证据支撑
4. **风险等级准确性**：风险等级必须与具体分析匹配
5. **格式规范性**：输出格式必须符合要求

# 输出要求：
- 如果原始结果符合标准，设置 needs_revision = false
- 如果需要修改，设置 needs_revision = true 并在 revised_output 中提供完整的修改版本
- 在 revision_reasons 中详细说明修改原因
- revised_output 必须是完整的GenericDomainJudgement格式，包含所有signals和overall

请专注于{domain_key}的特定要求进行审查。
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
    
    def _get_default_standards(self) -> Dict[str, str]:
        """获取默认的审查标准"""
        return {
            'domain_1': """
# Domain 1 (随机化过程) 审查标准：

## Signal检查要求：
1. **随机序列生成**：必须明确识别并评估随机序列生成方法
2. **分配隐藏**：必须评估分配隐藏的充分性
3. **基线差异**：必须考虑基线特征的平衡性

## Overall风险判断要求：
- Low risk: 随机序列生成方法恰当且分配隐藏充分
- Some concerns: 随机化信息不充分但无明显偏差迹象  
- High risk: 随机化方法不当或分配隐藏不充分

## 常见错误：
- 混淆随机序列生成和分配隐藏
- 仅基于"随机"一词就判断为低风险
- 忽视基线特征失衡的影响
""",
            'domain_2': """
# Domain 2 (意向偏差) 审查标准：

## 分析路径要求：
- **Assignment路径**：关注分配到干预组的影响
- **Adherence路径**：关注依从干预的影响

## Signal检查要求：
1. **偏离识别**：必须识别偏离预期干预的情况
2. **偏离影响**：必须评估偏离对结果的潜在影响  
3. **分析方法**：必须评估ITT分析的充分性

## Overall风险判断要求：
- Low risk: 无重要偏离或偏离不影响结果
- Some concerns: 有偏离但影响有限
- High risk: 重要偏离且可能影响结果

## 常见错误：
- 混淆assignment和adherence分析
- 忽视ITT分析的重要性
- 低估偏离的潜在影响
""",
            'domain_3': """
# Domain 3 (缺失数据) 审查标准：

## Signal检查要求：
1. **缺失比例**：必须评估缺失数据的比例和模式
2. **缺失原因**：必须考虑缺失数据的原因
3. **处理方法**：必须评估缺失数据处理方法的充分性

## Overall风险判断要求：
- Low risk: 缺失数据很少或处理方法充分
- Some concerns: 中等缺失但处理合理
- High risk: 大量缺失或处理方法不当

## 常见错误：
- 仅关注缺失比例而忽视缺失机制
- 未评估敏感性分析的充分性
- 混淆不同类型的缺失数据
""",
            'domain_4': """
# Domain 4 (结果测量) 审查标准：

## Signal检查要求：
1. **测量方法**：必须评估结果测量方法的适当性
2. **测量一致性**：必须评估测量在组间的一致性
3. **盲法有效性**：必须评估盲法对测量的影响

## Overall风险判断要求：
- Low risk: 测量方法客观且一致
- Some concerns: 主观测量但有盲法保护
- High risk: 主观测量且无盲法保护

## 常见错误：
- 混淆客观和主观测量
- 忽视测量时机的重要性
- 高估盲法的保护作用
""",
            'domain_5': """
# Domain 5 (结果选择) 审查标准：

## Signal检查要求：
1. **预设计划**：必须评估是否有预设的分析计划
2. **多重比较**：必须考虑多重比较的影响
3. **选择性报告**：必须评估选择性报告的可能性

## Overall风险判断要求：
- Low risk: 有预设计划且严格遵循
- Some concerns: 计划不够详细但无明显选择性
- High risk: 无计划或明显的选择性报告

## 常见错误：
- 忽视试验注册信息
- 低估多重比较的影响
- 混淆结果和结局
""",
            'default': """
# 通用ROB2审查标准：

## 基本要求：
1. **逻辑一致性**：signals与overall必须逻辑一致
2. **证据充分性**：每个判断必须有充分证据支撑
3. **风险等级准确性**：风险等级必须与分析匹配
4. **格式规范性**：输出格式必须符合要求

## 风险等级标准：
- Low risk: 偏差风险很低
- Some concerns: 存在一些担忧但不严重
- High risk: 偏差风险很高

请严格按照ROB2框架进行审查。
"""
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 为了保持向后兼容，保留旧的类名作为别名
QualityCheckerAgent = DomainReviewerAgent