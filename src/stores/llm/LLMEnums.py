from enum import Enum


class LLMEnums(Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"
    GROQ = "GROQ"
    OPENROUTER="OPENROUTER"

class OpenAIEnums(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT ="assistant"

class CoHereEnums(Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    ASSISTANT ="CHATBOT"
    DOCUMENT = "search_document"
    QUERY = "search_query"

class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"


class GroqEnums(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT ="assistant"

class OpenRouterEnums(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT ="assistant"
