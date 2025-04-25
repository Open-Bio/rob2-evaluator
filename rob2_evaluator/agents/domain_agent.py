from rob2_evaluator.schema.rob2_schema import (
    DOMAIN_SCHEMAS,
    GenericDomainJudgement,
)
from rob2_evaluator.utils.llm import call_llm
from rob2_evaluator.llm.models import ModelProvider
from typing import List, Dict, Any

from jinja2 import Template


class DomainAgent:
    def __init__(
        self,
        domain_key: str,
        model_name="gemma3:27b",
        model_provider=ModelProvider.OLLAMA,
    ):
        self.domain_key = domain_key
        self.schema = DOMAIN_SCHEMAS[domain_key]
        self.model_name = model_name
        self.model_provider = model_provider

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
                page_display = page + 1
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
        prompt_template = """
# ROB2 Domain Evaluation Expert

## Task Background
You are an expert in the ROB2 framework, specializing in assessing risk of bias in randomized controlled trials (RCTs). Your task is to analyze the provided study content and evaluate the risk of bias for the domain: "{{ domain_title }}".

## Evaluation Materials
The following content has been extracted from the study. Each text block is clearly marked with its source page number using the format `[Page X]`.

{{ context }}

## Analysis Steps
1.  Carefully read all the provided material, paying close attention to the `[Page X]` markers.
2.  For each Signal Question below, provide an answer, a detailed reason, and supporting evidence.
3.  Provide an overall risk assessment for the domain, including the reason and supporting evidence.
4.  **Crucially**: When providing evidence (`evidence` field), you **must**:
    *   Quote the text **exactly** as it appears in the Evaluation Materials.
    *   Include the corresponding `page_idx` (the number X from the `[Page X]` marker) for **each** piece of evidence cited. Find the text segment in the material above and report its associated page number.

## Signal Questions
{% for s in signals_schema -%}
{{ s.id }}: {{ s.text }}
{% endfor %}

Answer options for each signal: {{ signal_options | join('/') }}

## Overall Risk Assessment
Domain-level risk of bias judgment options:
{% for opt in domain_options -%}
- {{ opt }}
{% endfor %}

## Required Output Format
Return **only** a valid JSON object adhering strictly to the following structure. Ensure all evidence includes both `text` and the correct `page_idx`.

```json
{
  "signals": {
    {% for s in signals_schema -%}
    "{{ s.id }}": {
      "answer": "<Select one: {{ signal_options | join('/') }}>",
      "reason": "<Your detailed reasoning for the answer>",
      "evidence": [
        {
          "text": "<Exact quote from the Evaluation Materials>",
          "page_idx": <Integer page number corresponding to the quote's source>
        }
        // Add more evidence items if needed, each with text and page_idx
      ]
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  },
  "overall": {
    "risk": "<Select one: {{ domain_options | join('/') }}>",
    "reason": "<Your detailed reasoning for the overall domain judgment>",
    "evidence": [
      {
        "text": "<Exact quote supporting the overall judgment>",
        "page_idx": <Integer page number corresponding to the quote's source>
      }
      // Add more evidence items if needed
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
