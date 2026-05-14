import json
from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError


ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_llm_json(raw_content: str, model_type: type[ModelT]) -> ModelT:
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"LLM returned invalid JSON: {exc.msg}",
        ) from exc

    try:
        return model_type.model_validate(parsed)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "LLM returned JSON that does not match the expected schema.",
                "errors": exc.errors(),
            },
        ) from exc
