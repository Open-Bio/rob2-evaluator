"""Helper functions for LLM"""

import json
from typing import TypeVar, Type, Optional, Any
from pydantic import BaseModel
from rob2_evaluator.utils.progress import progress
from rob2_evaluator.schema.rob2_schema import DefaultResponseFactory

T = TypeVar("T", bound=BaseModel)


def call_llm(
    prompt: Any,
    model_name: str,
    model_provider: str,
    pydantic_model: Type[T] = None,
    agent_name: Optional[str] = None,
    max_retries: int = 3,
    domain_key: Optional[str] = None,
) -> T:
    """
    Makes an LLM call with retry logic, handling both JSON supported and non-JSON supported models.

    Args:
        prompt: The prompt to send to the LLM
        model_name: Name of the model to use
        model_provider: Provider of the model
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates
        max_retries: Maximum number of retries (default: 3)
        domain_key: Optional domain key for creating default responses

    Returns:
        An instance of the specified Pydantic model
    """
    from rob2_evaluator.llm.models import get_model, get_model_info

    model_info = get_model_info(model_name)
    llm = get_model(model_name, model_provider)

    # 如果不需要结构化输出，直接返回字符串
    if pydantic_model is None:
        for attempt in range(max_retries):
            try:
                result = llm.invoke(prompt)
                # 兼容langchain返回结构
                if hasattr(result, "content"):
                    return result.content.strip()
                return str(result).strip()
            except Exception as e:
                if agent_name:
                    progress.update_status(
                        agent_name, None, f"Error - retry {attempt + 1}/{max_retries}"
                    )
                if attempt == max_retries - 1:
                    return "no"
        return "no"

    # For non-JSON support models, we can use structured output
    if not (model_info and not model_info.has_json_mode()):
        llm = llm.with_structured_output(
            pydantic_model,
            method="json_mode",
        )

    # Call the LLM with retries
    for attempt in range(max_retries):
        try:
            # Call the LLM
            result = llm.invoke(prompt)

            # For non-JSON support models, we need to extract and parse the JSON manually
            if model_info and not model_info.has_json_mode():
                parsed_result = extract_json_from_response(result.content)
                if parsed_result:
                    return pydantic_model(**parsed_result)
            else:
                return result

        except Exception as e:
            if agent_name:
                progress.update_status(
                    agent_name, None, f"Error - retry {attempt + 1}/{max_retries}"
                )

            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts: {e}")
                # Create default response using factory
                if domain_key:
                    return DefaultResponseFactory.create_response(
                        pydantic_model, domain_key
                    )
                # Fallback to basic default for non-domain models
                return create_basic_default(pydantic_model)

    return create_basic_default(pydantic_model)


def create_basic_default(model_class: Type[T]) -> T:
    """Creates a basic default response for non-domain models."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Some concerns"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif field_name == "evidence":
            default_values[field_name] = []
        elif field_name == "signals":
            default_values[field_name] = {
                "q1": {"answer": "NI", "reason": "No information", "evidence": []}
            }
        elif field_name == "overall":
            default_values[field_name] = {
                "risk": "Some concerns",
                "reason": "Insufficient information",
                "evidence": [],
            }
        elif (
            hasattr(field.annotation, "__origin__")
            and field.annotation.__origin__ == dict
        ):
            default_values[field_name] = {}
        elif (
            hasattr(field.annotation, "__origin__")
            and field.annotation.__origin__ == list
        ):
            default_values[field_name] = []
        else:
            # 处理自定义Pydantic模型
            if hasattr(field.annotation, "model_fields"):
                default_values[field_name] = create_basic_default(field.annotation)
            # 处理可选类型
            elif hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None

    return model_class(**default_values)


def extract_json_from_response(content: str) -> Optional[dict]:
    """Extracts JSON from markdown-formatted response."""
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]  # Skip past ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from response: {e}")
    return None
