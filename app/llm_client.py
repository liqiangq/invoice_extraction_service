import base64
import time
from typing import Any

from fastapi import HTTPException, status
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.config import Settings, settings


RETRYABLE_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, APIError)


class LLMClient:
    def __init__(self, app_settings: Settings = settings) -> None:
        if not app_settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OPENAI_API_KEY is not configured.",
            )

        self.settings = app_settings
        client_kwargs = {
            "api_key": app_settings.openai_api_key,
            "timeout": app_settings.llm_timeout_seconds,
        }
        if app_settings.openai_base_url:
            client_kwargs["base_url"] = app_settings.openai_base_url

        self.client = OpenAI(**client_kwargs)

    def extract_json(self, system_prompt: str, document_text: str) -> str:
        response_input = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Extract the requested data and return one JSON object only.\n\n{document_text}",
                    },
                ],
            },
        ]
        return self._create_response(system_prompt, response_input)

    def extract_json_from_image(self, system_prompt: str, image_bytes: bytes, media_type: str) -> str:
        image_data = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{media_type};base64,{image_data}"
        response_input = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Extract the invoice data from this invoice image and return one JSON object only.",
                    },
                    {
                        "type": "input_image",
                        "image_url": image_url,
                    },
                ],
            },
        ]
        return self._create_response(system_prompt, response_input)

    def _create_response(self, instructions: str, response_input: list[dict[str, Any]]) -> str:
        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.settings.model_name,
                    instructions=instructions,
                    input=response_input,
                    store=self.settings.llm_store_responses,
                    text={"format": {"type": "json_object"}},
                )
                content = self._response_text(response)
                if not content:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="LLM returned an empty response.",
                    )
                return content
            except AuthenticationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="OpenAI authentication failed. Check OPENAI_API_KEY in .env and restart the server.",
                ) from exc
            except BadRequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"OpenAI rejected the request: {exc.message}",
                ) from exc
            except APIStatusError as exc:
                raise HTTPException(
                    status_code=exc.status_code,
                    detail=f"OpenAI API error: {exc.message}",
                ) from exc
            except RETRYABLE_ERRORS as exc:
                last_error = exc
                if attempt >= self.settings.llm_max_retries:
                    break
                time.sleep(0.5 * (attempt + 1))

        if isinstance(last_error, APIConnectionError):
            detail = "Could not connect to OpenAI after retries. Check your internet connection, firewall, or VPN."
        elif isinstance(last_error, APITimeoutError):
            detail = "OpenAI request timed out after retries. Try a smaller image or try again."
        elif isinstance(last_error, RateLimitError):
            detail = "OpenAI rate limit was hit after retries. Wait briefly and try again."
        elif last_error is not None:
            detail = f"OpenAI request failed after retries: {last_error.__class__.__name__}."
        else:
            detail = "OpenAI request failed after retries."

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from last_error

    @staticmethod
    def _response_text(response: Any) -> str | None:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        for output_item in getattr(response, "output", []) or []:
            for content_item in getattr(output_item, "content", []) or []:
                text = getattr(content_item, "text", None)
                if text:
                    return text

        return None
