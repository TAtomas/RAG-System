from ..LLMInterface import LLMInterface
from groq import Groq
from ..LLMEnums import OpenAIEnums,GroqEnums
import logging


class GroqProvider(LLMInterface):
    
    def __init__(self , api_key :str ,
                 api_url:str =None ,
                 default_max_input_characters :int=1000,
                 default_generation_max_output_tokens :int =1000,
                 default_generation_temperature:float =0.1
                 ):
        
        self.api_key=api_key
        self.api_url=api_url

        self.default_max_input_characters=default_max_input_characters
        self.default_generation_max_output_tokens=default_generation_max_output_tokens
        self.default_generation_temperature=default_generation_temperature

        self.generation_model_id =None
        self.embedding_model_id =None
        self.embedding_size =None

        self.client =Groq(api_key=self.api_key)
        self.enums=GroqEnums
        self.logger=logging.getLogger(__file__)


    def set_generation_model(self, model_id:str ):
        self.generation_model_id=model_id

    def set_embedding_model(self , model_id:str , embedding_size: int):
        self.logger.error("Groq have no embedding model")
        return None

    def process_text(self,text :str):
        return text[:self.default_max_input_characters].strip()


    def generate_text(self ,prompt :str ,chat_history :list=[],
                            max_output_token :int = None,temperature:float =None):
        if not self.client:
            self.logger.error("Groq Client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model was not set")
            return None

        max_output_token =max_output_token if max_output_token else self.default_generation_max_output_tokens
        temperature =temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt=prompt ,role= GroqEnums.USER.value)
        )

        response =self.client.chat.completions.create(
            model=self.generation_model_id,
            messages =chat_history,
            max_tokens= max_output_token,
            temperature=temperature
        )

        if not response or not response.choices or len(response.choices) == 0 or not response.choices[0].message:
            self.logger.error("error while generate tokens with Groq")
            return None

        return response.choices[0].message.content

    
    def embed_text(self ,text :str ,document_type :str = None):
        self.logger.error("Groq have no embedding model")
        return None


    def construct_prompt(self , prompt :str ,role :str):
        return {
            "role":role,
            "content":self.process_text(text=prompt)
        }
