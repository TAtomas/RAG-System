from enum import Enum


class LLMEnums(Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"

class OpenAIEnums(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT ="assistant"