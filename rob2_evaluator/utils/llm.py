"""Helper functions for LLM - Optimized default value generation"""

import json
import logging
from typing import Any, Optional, Type, TypeVar, Union, get_args, get_origin
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from rob2_evaluator.schema.rob2_schema import DefaultResponseFactory
from rob2_evaluator.utils.progress import progress

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
            except Exception:
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
                logging.error(f"Error in LLM call after {max_retries} attempts: {e}")
                logging.error(f"Model: {model_name}, Provider: {model_provider}")
                logging.error(f"Pydantic model: {pydantic_model}")

                # 优先使用领域schema的默认响应
                if domain_key:
                    try:
                        default_response = DefaultResponseFactory.create_response(
                            pydantic_model, domain_key
                        )
                        logging.info(f"Using domain default response for {domain_key}")
                        return default_response
                    except Exception as domain_err:
                        logging.warning(
                            f"Domain default failed: {domain_err}, falling back to basic default"
                        )

                # Fallback to basic default for non-domain models
                default_response = create_basic_default(pydantic_model)
                logging.info(
                    f"Using basic default response for {pydantic_model.__name__}"
                )
                return default_response

    # 最终兜底也保持一致
    if domain_key:
        try:
            default_response = DefaultResponseFactory.create_response(
                pydantic_model, domain_key
            )
            logging.info(
                f"Final fallback: using domain default response for {domain_key}"
            )
            return default_response
        except Exception:
            pass

    default_response = create_basic_default(pydantic_model)
    logging.info(
        f"Final fallback: using basic default response for {pydantic_model.__name__}"
    )
    return default_response


def create_basic_default(model_class: Type[T]) -> T:
    """
    Creates a basic default response for any Pydantic model.

    This function intelligently generates default values based on:
    1. Field default values if present
    2. Field types and annotations
    3. Common field naming patterns
    4. Validation requirements
    """
    # Special handling for specific models
    if hasattr(model_class, "__name__"):
        if model_class.__name__ == "ReviewResult":
            return _create_review_result_default(model_class)

    default_values = {}

    for field_name, field_info in model_class.model_fields.items():
        # Try to get the default value for this field
        default_value = _get_field_default_value(field_name, field_info, model_class)

        # Only add to default_values if we got a non-None value or the field is Optional
        if default_value is not None or _is_optional_field(field_info):
            default_values[field_name] = default_value

    try:
        # Try to create the model with our default values
        result = model_class(**default_values)
        logging.debug(f"Created default for {model_class.__name__}: {result}")
        return result
    except Exception as e:
        logging.warning(f"First attempt failed for {model_class.__name__}: {e}")

        # If that fails, try with minimal required fields only
        minimal_values = _get_minimal_required_fields(model_class)
        try:
            result = model_class(**minimal_values)
            logging.debug(
                f"Created minimal default for {model_class.__name__}: {result}"
            )
            return result
        except Exception as e2:
            logging.error(f"Failed to create default for {model_class.__name__}: {e2}")
            logging.error(f"Attempted values: {default_values}")
            logging.error(f"Minimal values: {minimal_values}")
            raise


def _create_review_result_default(model_class: Type[T]) -> T:
    """Creates a proper default ReviewResult object."""
    default_values = {
        "needs_revision": False,
        "revision_reasons": [],
        "revised_output": None,
        "confidence": 0.0,
    }
    logging.debug(f"Creating ReviewResult default: {default_values}")
    return model_class(**default_values)


def _get_field_default_value(
    field_name: str, field_info: FieldInfo, model_class: Type[BaseModel]
) -> Any:
    """
    Get appropriate default value for a field based on its type and metadata.

    Priority order:
    1. Field's explicit default value
    2. Field's default_factory
    3. Smart defaults based on field name
    4. Type-based defaults
    """

    # 1. Check for explicit default value
    if (
        field_info.default is not None and field_info.default != ...
    ):  # ... is Pydantic's required marker
        return field_info.default

    # 2. Check for default_factory
    if field_info.default_factory is not None:
        try:
            return field_info.default_factory()
        except Exception:
            pass

    # 3. Get the actual type annotation
    annotation = field_info.annotation

    # 4. Smart defaults based on field name patterns
    smart_default = _get_smart_default_by_name(field_name, annotation)
    if smart_default is not None:
        return smart_default

    # 5. Type-based defaults
    return _get_default_by_type(annotation, field_name)


def _get_smart_default_by_name(field_name: str, annotation: Any) -> Any:
    """
    Returns smart defaults based on common field naming patterns.
    """
    field_lower = field_name.lower()

    # Boolean patterns
    if any(
        field_lower.startswith(prefix)
        for prefix in ["is_", "has_", "should_", "can_", "will_"]
    ):
        return False
    if field_lower.endswith("_enabled") or field_lower.endswith("_active"):
        return False
    if field_lower == "needs_revision":
        return False

    # String patterns
    if annotation in (str, Optional[str]) or _get_origin_safe(annotation) is Union:
        if "name" in field_lower:
            return "Default"
        if "description" in field_lower:
            return "No description"
        if "reason" in field_lower:
            return "No specific reason provided"
        if "message" in field_lower or "msg" in field_lower:
            return "No message"
        if "comment" in field_lower:
            return "No comment"
        if field_lower in ["risk", "level", "severity"]:
            return "Low"
        if field_lower in ["status", "state"]:
            return "Unknown"
        if "evidence" in field_lower and annotation == str:
            return "No evidence provided"

    # Numeric patterns
    if annotation in (int, float, Optional[int], Optional[float]):
        if "count" in field_lower or "number" in field_lower or "num_" in field_lower:
            return 0
        if "score" in field_lower or "rating" in field_lower:
            return 0.0 if annotation in (float, Optional[float]) else 0
        if "confidence" in field_lower or "probability" in field_lower:
            return 0.0
        if "threshold" in field_lower:
            return 0.5 if annotation in (float, Optional[float]) else 1

    # List/Array patterns
    origin = _get_origin_safe(annotation)
    if origin in (list, List):
        if (
            "reasons" in field_lower
            or "errors" in field_lower
            or "warnings" in field_lower
        ):
            return []
        if "evidence" in field_lower:
            return []
        if "items" in field_lower or "elements" in field_lower:
            return []

    # Dict patterns
    if origin in (dict, Dict):
        if "signals" in field_lower:
            return {"q1": {"answer": "NI", "reason": "No information", "evidence": []}}
        if "overall" in field_lower:
            return {"risk": "Low", "reason": "Insufficient information", "evidence": []}
        if "metadata" in field_lower or "data" in field_lower:
            return {}

    return None


def _get_default_by_type(annotation: Any, field_name: str = "") -> Any:
    """
    Returns default value based on type annotation.
    """
    # Handle None type
    if annotation is type(None):
        return None

    # Basic types
    if annotation is str:
        return ""
    elif annotation is bool:
        return False
    elif annotation is int:
        return 0
    elif annotation is float:
        return 0.0
    elif annotation is bytes:
        return b""

    # Standard library types
    elif annotation is Decimal:
        return Decimal("0")
    elif annotation is datetime:
        return datetime.now()
    elif annotation is date:
        return date.today()
    elif annotation is time:
        return time()
    elif annotation is UUID:
        return UUID("00000000-0000-0000-0000-000000000000")

    # Handle Optional and Union types
    origin = _get_origin_safe(annotation)
    args = get_args(annotation)

    if origin is Union:
        # For Optional[T] (Union[T, None]), try to get default for T
        non_none_types = [arg for arg in args if arg is not type(None)]
        if len(non_none_types) == 1:
            # This is Optional[T]
            return _get_default_by_type(non_none_types[0], field_name)
        elif len(non_none_types) > 1:
            # Multiple types, try the first one
            return _get_default_by_type(non_none_types[0], field_name)
        else:
            # All None? Return None
            return None

    # Collections
    elif origin in (list, List):
        return []
    elif origin in (set, Set):
        return set()
    elif origin in (tuple, Tuple):
        if args:
            # For Tuple with specific types, create tuple with defaults
            return tuple(_get_default_by_type(arg, "") for arg in args if arg != ...)
        return ()
    elif origin in (dict, Dict):
        return {}

    # Enums
    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        # Return first enum value
        return list(annotation)[0] if list(annotation) else None

    # Pydantic models
    elif isinstance(annotation, type) and issubclass(annotation, BaseModel):
        try:
            # Recursively create default for nested model
            return create_basic_default(annotation)
        except Exception:
            return None

    # Literal types (Python 3.8+)
    try:
        from typing import Literal

        if origin is Literal:
            # Return the first literal value
            return args[0] if args else None
    except ImportError:
        pass

    # If we can't determine the type, return None for Optional fields, empty string for others
    return None


def _is_optional_field(field_info: FieldInfo) -> bool:
    """
    Check if a field is Optional (can be None).
    """
    annotation = field_info.annotation
    origin = _get_origin_safe(annotation)

    if origin is Union:
        args = get_args(annotation)
        return type(None) in args

    # Check if field has a default of None
    return field_info.default is None


def _get_minimal_required_fields(model_class: Type[BaseModel]) -> dict:
    """
    Get minimal set of required fields with basic defaults.
    This is a last resort when normal default generation fails.
    """
    minimal = {}

    for field_name, field_info in model_class.model_fields.items():
        # Only include required fields (no default value)
        if field_info.default is ... and field_info.default_factory is None:
            annotation = field_info.annotation

            # Provide most basic possible defaults
            if annotation is str:
                minimal[field_name] = ""
            elif annotation is bool:
                minimal[field_name] = False
            elif annotation is int:
                minimal[field_name] = 0
            elif annotation is float:
                minimal[field_name] = 0.0
            elif _get_origin_safe(annotation) in (list, List):
                minimal[field_name] = []
            elif _get_origin_safe(annotation) in (dict, Dict):
                minimal[field_name] = {}
            else:
                # For complex types, try None if possible
                if _is_optional_field(field_info):
                    minimal[field_name] = None
                else:
                    # Last resort: try to instantiate the type
                    try:
                        if isinstance(annotation, type) and issubclass(
                            annotation, BaseModel
                        ):
                            minimal[field_name] = create_basic_default(annotation)
                        else:
                            minimal[field_name] = None
                    except Exception:
                        minimal[field_name] = None

    return minimal


def _get_origin_safe(annotation: Any) -> Any:
    """
    Safely get the origin of a type annotation.
    Handles both typing and types.GenericAlias.
    """
    origin = get_origin(annotation)
    if origin is not None:
        return origin

    # For Python 3.9+ where list, dict, etc. can be used directly
    if hasattr(annotation, "__origin__"):
        return annotation.__origin__

    # Handle built-in generic types
    if annotation is list:
        return list
    elif annotation is dict:
        return dict
    elif annotation is set:
        return set
    elif annotation is tuple:
        return tuple

    return None


def extract_json_from_response(content: str) -> Optional[dict]:
    """Extracts JSON from markdown-formatted response."""
    try:
        # Try to find JSON in markdown code blocks
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]  # Skip past ```json
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)

        # Try to find JSON without markdown
        json_start = content.find("{")
        if json_start != -1:
            # Find the matching closing brace
            brace_count = 0
            json_end = -1
            for i, char in enumerate(content[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end != -1:
                json_text = content[json_start:json_end]
                return json.loads(json_text)

    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON: {e}")
    except Exception as e:
        logging.error(f"Error extracting JSON from response: {e}")

    return None


# Add these imports at the top if not already present
from typing import Dict, List, Set, Tuple

try:
    from typing import Literal
except ImportError:
    Literal = None  # For Python < 3.8
