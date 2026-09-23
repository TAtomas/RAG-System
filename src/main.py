from fastapi import FastAPI 
from routes import base,data,nlp
from motor.motor_asyncio import  AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser

app = FastAPI()

@app.on_event("startup")
async def startup_span():
    settings =get_settings()

    app.mongo_conn =AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client =app.mongo_conn[settings.MONGODB_DATABASE]

    LLMProviderFactory_init=LLMProviderFactory(settings)
    VectorDBProviderFactory_init=VectorDBProviderFactory(settings)
   #set generation model 

    app.generation_client = LLMProviderFactory_init.create(provider=settings.GENERATION_BACKEND_TEST_PROVIDER)
    app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

   #set enedding model 
    app.embedding_client = LLMProviderFactory_init.create(provider=settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,embedding_size=settings.EMBEDDING_MODEL_SIZE)

    #Set Vector Database
    app.vector_db_client =VectorDBProviderFactory_init.create(provider=settings.VECTOR_DB_BACKEND)
    app.vector_db_client.connect()

    #set language
    app.template_parser=TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
        )   

@app.on_event("shutdown")
async def shutdown_span():
    app.mongo_conn.close()
    app.vector_db_client.disconnect()



app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)
