from rob2_evaluator.schema.rob2_schema import (
    DOMAIN_SCHEMAS,
    GenericDomainJudgement,
)
from rob2_evaluator.config.model_config import ModelConfig
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any, Optional

from jinja2 import Template


class DomainAgent:
    def __init__(
        self,
        domain_key: str,
        model_name: Optional[str] = None,
        model_provider: Optional[ModelProvider] = None,
    ):
        self.domain_key = domain_key
        self.schema = DOMAIN_SCHEMAS[domain_key]

        config = ModelConfig()
        # 优先使用传入的参数，其次使用配置值
        self.model_name = model_name or config.get_model_name()
        self.model_provider = model_provider or config.get_model_provider()
        print(
            f"Using model: {self.model_name} from provider: {self.model_provider.name}"
        )

    def evaluate(self, items: List[Dict[str, Any]]):
        signals_schema = self.schema["signals"]
        prompt = self._build_prompt(items, signals_schema)

        # 调用 LLM，使用更新后的 Pydantic 模型进行解析
        result: GenericDomainJudgement = call_llm(
            prompt=prompt,
            model_name=self.model_name,
            model_provider=self.model_provider,
            pydantic_model=GenericDomainJudgement,
            domain_key=self.domain_key,
        )

        # 直接处理包含 page_idx 的结果
        processed_signals = {}
        for signal_id, signal_data in result.signals.items():
            processed_evidence = []
            for ev in signal_data.evidence:
                # ev 已经是 EvidenceItem
                processed_evidence.append(
                    {
                        "text": ev.text,
                        "page_idx": ev.page_idx if ev.page_idx is not None else -1,
                    }
                )

            processed_signals[signal_id] = {
                "answer": signal_data.answer,
                "reason": signal_data.reason,
                "evidence": processed_evidence,
            }

        processed_overall_evidence = []
        for ev in result.overall.evidence:
            processed_overall_evidence.append(
                {
                    "text": ev.text,
                    "page_idx": ev.page_idx if ev.page_idx is not None else -1,
                }
            )

        return {
            "domain_key": self.domain_key,  # 添加domain_key用于质量检查
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
        """使用 Jinja2 模板构建 prompt，要求 LLM 返回 page_idx"""
        # 构建带有页码标记的上下文
        context_lines = []
        for item in items:
            page = item.get("page_idx", "?")  # 如果意外缺失 page_idx，用 '?' 替代
            # 这里将 page_idx 加 1（如果是数字）
            if isinstance(page, int):
                page_display = page
            else:
                page_display = page
            text = item.get("text", "")
            context_lines.append(f"[Page {page_display}] {text}")
        context = "\n\n".join(context_lines)  # 使用双换行符分隔段落可能更清晰

        # 获取 schema 信息
        signal_options = signals_schema[0]["options"]  # 假设所有信号选项相同
        domain_options = self.schema["domain_options"]
        domain_title = self.schema["domain_name"]

        # 更新后的 Jinja2 模板字符串
        prompt_template = prompt_template = """
# Persona and Objective
You are an expert auditor specializing in the Cochrane Risk of Bias 2 (ROB2) framework. Your objective is to assess the risk of bias for the `{{ domain_title }}` domain by analyzing the provided text and completing the JSON output. You have a deep, built-in understanding of the ROB2 judgment algorithms.

## Core Directives (You MUST follow these rules)
1.  **Evidence is Supreme**: Base all judgments **exclusively** on the text provided in the `Evaluation Materials`. Do not use external knowledge or make assumptions about what is "usually" done in research.
2.  **Absence of Information is NOT Evidence of a Flaw**: This is your most important principle. A 'High Risk' judgment requires **positive textual evidence of a problem** (e.g., the text *states* a flawed method was used). A lack of detail about a correct method should lead to a 'No Information' (`NI`) response for that question, which typically results in an overall judgment of 'Some Concerns', not 'High Risk'.
3.  **Act as a Literal Auditor, Not an Interpretive Detective**: Your job is to report what the text says, not what you think it implies.
    - Quote text verbatim for evidence.
    - Do not infer meaning beyond what is explicitly stated.
    - If the text is ambiguous, note the ambiguity in your `reason` field rather than defaulting to a worst-case conclusion.
4.  **Strictly Adhere to the Output Format**: Provide **only** the JSON object in your response. Do not include any introductory text, explanations, or apologies outside of the JSON structure.

## Evaluation Materials
The following content has been extracted from the study. Each text block is clearly marked with its source page number using the format `[Page X]`.

{{ context }}

## Task Workflow
1.  **Review the `Core Directives`** to set your operational parameters.
2.  **Thoroughly read all `Evaluation Materials`**.
3.  For each `Signal Question`, provide an `answer`, a detailed `reason`, and supporting `evidence`.
4.  Apply your internal ROB2 algorithm knowledge to determine the `overall` risk based on your signal question answers.
5.  Construct the final JSON object exactly as specified below.

## Signal Questions and Options
- Signal Questions:
{% for s in signals_schema -%}
  - {{ s.id }}: {{ s.text }}
{% endfor %}
- Answer Options: {{ signal_options | join('/') }}

## Overall Risk Assessment Options
- {{ domain_options | join(', ') }}

## Required Output Format
Return **only** a valid JSON object adhering strictly to the following structure.

```json
{
  "signals": {
    {% for s in signals_schema -%}
    "{{ s.id }}": {
      "answer": "<Select one: {{ signal_options | join('/') }}>",
      "reason": "<Your detailed reasoning based strictly on the provided text and core directives>",
      "evidence": [
        {
          "text": "<Exact quote from the Evaluation Materials>",
          "page_idx": "<Integer page number corresponding to the quote's source>"
        }
      ]
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  },
  "overall": {
    "risk": "<Select one: {{ domain_options | join('/') }}>",
    "reason": "<Your summary reasoning, explaining how the answers to the signal questions lead to this overall judgment based on the ROB2 algorithm>",
    "evidence": [
      {
        "text": "<The most critical quote(s) supporting the overall judgment>",
        "page_idx": "<Integer page number for the quote>"
      }
    ]
  }
}
```
"""
        template = Template(
            prompt_template, trim_blocks=True, lstrip_blocks=True
        )  # trim/lstrip helps clean up whitespace
        prompt = template.render(
            context=context,
            signals_schema=signals_schema,
            signal_options=signal_options,
            domain_options=domain_options,
            domain_title=domain_title,
        )

        # print(f"DEBUG: Generated Prompt:\n{prompt[:1000]}...")
        return prompt


# 简单使用示例
if __name__ == "__main__":
    # 创建域代理实例
    from rob2_evaluator.schema.rob2_schema import DomainKey

    agent = DomainAgent(domain_key=DomainKey.RANDOMIZATION)

    # 准备测试数据 - 模拟从PDF提取的文本片段
    test_items = [
        {"text": "参与者按照计算机生成的随机序列分配到实验组或对照组。", "page_idx": 2},
        {
            "text": "分配隐藏采用密封不透明信封方法，研究人员无法预知分配结果。",
            "page_idx": 2,
        },
        {"text": "基线特征在两组间无显著差异，表明随机化成功。", "page_idx": 4},
    ]

    # 执行评估
    result = agent.evaluate(test_items)

    # 输出结果
    print(f"评估域: {result['domain']}")
    print(f"整体风险: {result['overall']['risk']}")
    print(f"信号问题数量: {len(result['signals'])}")

    # 显示第一个信号的详细信息
    first_signal = list(result["signals"].values())[0]
    print(f"第一个信号答案: {first_signal['answer']}")
    print(f"证据数量: {len(first_signal['evidence'])}")
