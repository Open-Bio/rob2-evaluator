"""
ROB2评估审查标准配置模块

此模块提供了配置审查标准的功能，允许用户自定义每个domain的检查标准。
"""

from typing import Dict, Optional
import json
from pathlib import Path
from rob2_evaluator.schema.rob2_schema import DomainKey


class ReviewConfig:
    """审查配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化审查配置

        Args:
            config_path: 自定义配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self._standards = self._load_standards()

    def _load_standards(self) -> Dict[str, str]:
        """加载审查标准"""
        if self.config_path and Path(self.config_path).exists():
            return self._load_from_file(self.config_path)
        else:
            return self._get_default_standards()

    def _load_from_file(self, file_path: str) -> Dict[str, str]:
        """从文件加载审查标准"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                return config_data.get(
                    "review_standards", self._get_default_standards()
                )
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}")
            return self._get_default_standards()

    def get_standards(self) -> Dict[str, str]:
        """获取审查标准"""
        return self._standards.copy()

    def update_standard(self, domain_key: str, standard: str) -> None:
        """更新特定domain的审查标准"""
        self._standards[domain_key] = standard

    def save_to_file(self, file_path: str) -> None:
        """保存配置到文件"""
        config_data = {
            "review_standards": self._standards,
            "description": "ROB2评估审查标准配置文件",
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到: {file_path}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def _get_default_standards(self) -> Dict[str, str]:
        """获取默认的审查标准"""
        return {
            DomainKey.RANDOMIZATION: """
# Domain 1 (随机化过程) 审查标准：

## 必须检查的要点：
1. **随机序列生成方法**
   - 计算机随机数生成器（低风险）
   - 随机数表（低风险）
   - 抛硬币、掷骰子（低风险）
   - 简单交替、日期/姓名（高风险）
   - 信息不充分（一些担忧）

2. **分配隐藏**
   - 中央随机化、密封信封（低风险）
   - 开放随机化表（高风险）
   - 信息不充分（一些担忧）

3. **基线特征平衡**
   - 组间基线特征是否平衡
   - 重要预后因子的分布

## 判断标准：
- Low risk: 随机序列生成恰当且分配隐藏充分
- Some concerns: 随机化信息不充分但无明显问题
- High risk: 随机化方法不当或分配隐藏失败

## 常见错误要求纠正：
- 仅因提到"随机"就判断为低风险
- 混淆随机序列生成和分配隐藏
- 忽视基线失衡的重要性
""",
            DomainKey.DEVIATION_ASSIGNMENT: """
# Domain 2 (意向偏差) 审查标准：

## 分析类型判断：
- **Assignment分析**: 关注分配到干预组的效果
- **Adherence分析**: 关注依从干预的效果

## 必须评估的要点：
1. **偏离识别**
   - 偏离干预的参与者比例
   - 偏离类型（停止干预、接受其他干预等）
   - 偏离是否与结果相关

2. **分析方法**
   - ITT分析的实施充分性
   - Per-protocol分析的合理性
   - 偏离处理的恰当性

3. **偏离影响**
   - 偏离对结果的潜在影响
   - 组间偏离的平衡性

## 判断标准：
- Low risk: 无重要偏离或偏离不影响结果
- Some concerns: 有偏离但影响可能有限
- High risk: 重要偏离且可能实质性影响结果

## 必须纠正的错误：
- 混淆assignment和adherence分析
- 忽视ITT分析的重要性
- 低估偏离的潜在影响
""",
            DomainKey.DEVIATION_ADHERENCE: """
# Domain 2 (意向偏差-依从性分析) 审查标准：

## 分析类型判断：
- **Adherence分析**: 关注依从干预的效果

## 必须评估的要点：
1. **依从性偏离识别**
   - 未按计划接受干预的参与者比例
   - 依从性相关的偏离类型
   - 依从性偏离是否与结果相关

2. **分析方法**
   - Per-protocol分析的实施
   - 依从性调整分析的恰当性
   - 偏离处理的合理性

3. **偏离影响**
   - 依从性偏离对结果的潜在影响
   - 组间依从性的比较

## 判断标准：
- Low risk: 依从性好或偏离不影响结果
- Some concerns: 有依从性问题但影响有限
- High risk: 严重依从性问题且可能影响结果

## 必须纠正的错误：
- 混淆assignment和adherence分析
- 忽视依从性对结果的影响
- 低估依从性偏离的重要性
""",
            DomainKey.MISSING_DATA: """
# Domain 3 (缺失数据) 审查标准：

## 必须评估的要点：
1. **缺失数据比例**
   - 各组缺失数据的比例
   - 缺失模式的分析
   - 总体失访率

2. **缺失原因**
   - 缺失是否与真实结果相关
   - 缺失原因在组间是否平衡
   - 缺失机制(MCAR/MAR/MNAR)

3. **处理方法**
   - 缺失数据插补方法
   - 敏感性分析的实施
   - 完整案例分析的合理性

## 判断标准：
- Low risk: 无缺失或缺失很少且处理恰当
- Some concerns: 缺失适中但处理合理
- High risk: 大量缺失或处理方法不当

## 必须纠正的错误：
- 仅关注比例忽视缺失机制
- 未充分评估敏感性分析
- 混淆不同类型的缺失数据
""",
            DomainKey.MEASUREMENT: """
# Domain 4 (结果测量) 审查标准：

## 必须评估的要点：
1. **测量方法特征**
   - 客观测量 vs 主观测量
   - 测量工具的可靠性
   - 测量时机的一致性

2. **测量者盲法**
   - 结果评估者是否知晓分组
   - 盲法实施的有效性
   - 盲法失败的可能性

3. **测量一致性**
   - 测量方法在组间是否一致
   - 测量环境的标准化
   - 测量者间一致性

## 判断标准：
- Low risk: 客观测量或主观测量有充分盲法保护
- Some concerns: 主观测量但有一定盲法保护
- High risk: 主观测量且无盲法保护

## 必须纠正的错误：
- 混淆客观和主观测量
- 高估盲法的保护效果
- 忽视测量时机的重要性
""",
            DomainKey.SELECTION: """
# Domain 5 (结果选择) 审查标准：

## 必须评估的要点：
1. **预设分析计划**
   - 是否有预先制定的分析计划
   - 试验注册信息的一致性
   - 分析方法的预设性

2. **多重比较**
   - 多个结局的比较
   - 亚组分析的多重性
   - 统计检验的多重性

3. **选择性报告**
   - 结果报告的完整性
   - 不利结果的报告
   - 数据驱动的分析选择

## 判断标准：
- Low risk: 有详细预设计划且严格遵循
- Some concerns: 计划不够详细但无明显选择性
- High risk: 无计划或明显选择性报告

## 必须纠正的错误：
- 忽视试验注册的重要性
- 低估多重比较的影响
- 混淆主要和次要结局
""",
            "default": """
# 通用ROB2审查标准：

## 基本要求：
1. **逻辑一致性**: signals与overall判断必须逻辑一致
2. **证据充分性**: 每个判断必须有充分证据支撑
3. **风险等级准确性**: 风险等级必须与具体分析匹配
4. **格式规范性**: 输出格式必须符合GenericDomainJudgement要求

## 风险等级标准：
- **Low risk**: 偏差风险很低，研究设计和实施恰当
- **Some concerns**: 存在一些担忧，但偏差风险不高
- **High risk**: 偏差风险很高，结果可信度受到严重影响

## 通用检查要求：
1. 每个signal的answer必须明确(Yes/Probably yes/Probably no/No/No information)
2. 每个判断的reason必须详细且逻辑清晰
3. evidence必须具体且支撑判断
4. overall risk必须基于signals的综合分析

请严格按照ROB2框架标准进行审查和重写。
""",
        }


def create_sample_config_file(file_path: str = "review_standards.json") -> None:
    """创建示例配置文件"""
    config = ReviewConfig()
    config.save_to_file(file_path)
    print(f"示例配置文件已创建: {file_path}")
    print("你可以编辑此文件来自定义审查标准")


def load_custom_standards(file_path: str) -> Dict[str, str]:
    """加载自定义审查标准的便捷函数"""
    config = ReviewConfig(file_path)
    return config.get_standards()


if __name__ == "__main__":
    # 创建示例配置文件
    create_sample_config_file()
