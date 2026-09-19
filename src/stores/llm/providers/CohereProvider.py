from ..LLMInterface import LLMInterface
from ..LLMEnums import CoHereEnums,DocumentTypeEnum
import cohere
import logging

class CoHereProvider(LLMInterface):

    def __init__(self , api_key :str ,
                    default_max_input_characters :int=1000,
                    default_generation_max_output_tokens :int =1000,
                    default_generation_temperature:float =0.1
                    ):
        
        self.api_key=api_key
       
        self.default_max_input_characters=default_max_input_characters
        self.default_generation_max_output_tokens=default_generation_max_output_tokens
        self.default_generation_temperature=default_generation_temperature

        self.generation_model_id =None
        self.embedding_model_id =None
        self.embedding_size =None

        self.client=cohere.Client(api_key=self.api_key)

        logger= logging.getLogger(__file__)

    def set_generation_model(self, model_id:str ):
        self.generation_model_id=model_id

    def set_embedding_model(self , model_id:str , embedding_size: int):
        self.embedding_model_id =model_id
        self.embedding_size =embedding_size

    def process_text(self,text :str):
        return text[:self.default_max_input_characters].strip()

    def generate_text(self ,prompt :str ,chat_history :list=[],
                            max_output_token :int = None,temperature:float =None):
        if not self.client:
            self.logger.error("OPENAI Client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model was not set")
            return None
       
        
        max_output_token =max_output_token if max_output_token else self.default_generation_max_output_tokens
        temperature =temperature if temperature else self.default_generation_temperature

        response =self.client.chat(
            model= self.generation_model_id,
            chat_history=chat_history,
            message=self.process_text(self.process_text),
            temperature =temperature,
            max_tokens=max_output_token
            )
    
        if not response or not response.text:
             self.logger.error("error while generate tokens with CoHere")
             return None
        return response.text


    def embed_text(self ,text :str ,document_type :str = None):
        if not self.client:
            self.logger.error("OPENAI Client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("Embedding model was not set")
            return None
        input_type = CoHereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CoHereEnums.QUERY.value
        response=self.client.embed(
            model=self.embedding_model_id,
            texts=[self.process_text(text)],
            input_type=input_type,
            embedding_types=['float']
        )
        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("error while embedding text with CoHere")
            return None

        return response.embeddings.float


    def construct_prompt(self , prompt :str ,role :str):
        return {
            "role":role,
            "content":self.process_text(text=prompt)
        }