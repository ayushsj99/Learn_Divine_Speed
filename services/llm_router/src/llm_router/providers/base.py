from abc import ABC, abstractmethod
from typing import Literal


class BaseProvider(ABC):
    @abstractmethod
    async def generate(
        self, model: str, prompt: str, response_format: Literal["text", "json"]
    ) -> str:
        """Returns raw text. If response_format == 'json', the text is expected
        to be a JSON-parseable string — parsing happens in main.py, not here."""
        raise NotImplementedError
