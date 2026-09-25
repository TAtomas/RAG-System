from fastapi import FastAPI,APIRouter,Depends,UploadFile,status ,Request
from fastapi.responses import JSONResponse
from routes.schemas.nlp import PushRequest,SearchRequest
from models.ProjectModel import ProjectModel
from controllers import NLPController
from models.ChunkModel import ChunkModel
from models.enums import ResponseSignal
import logging

logger =logging.getLogger('uvicorn.error')

nlp_router =APIRouter(
    prefix="/api/v1/nlp",
    tags =["api_v1" ,"nlp"]
)
idx = 0
@nlp_router.post("/index/push/{project_id}")
async def index_project(request:Request,project_id:str ,push_request:PushRequest):
    global idx
    project_model =await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    chunk_model =await ChunkModel.create_instance(
         db_client=request.app.db_client
    )
    project =await project_model.get_project_or_create_one(
        Project_id=project_id
    )

    if not project:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROJECT_NOT_FOUND_ERROR.value
            }
        )
    nlp_controller =NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    has_record=True
    page_no=1
    inserted_items_count=0
    #idx=0
   
    while has_record :
        page_chunks=await chunk_model.get_project_chunks(project_id=project.id,page_no=page_no)
        if len(page_chunks):
            page_no+=1

        if not page_chunks or len(page_chunks) == 0:
            has_record=False
            break
        chunks_ids =  list(range(idx, idx + len(page_chunks)))
        idx += len(page_chunks)
        is_inserted=False
        try:
            is_inserted=nlp_controller.index_into_vector_db(
                project=project,
                chunks=page_chunks,
                chunks_ids=chunks_ids,
                do_reset=push_request.do_reset
            )
            inserted_items_count+=len(page_chunks)
            logger.info(f"chunk id: {page_chunks[0].id}")
            logger.info(f"Index result: {is_inserted}")
            logger.info(f"Chunks count: {len(page_chunks)}")
            logger.info(f"inserted count: {inserted_items_count}")
        except Exception as e:
            logger.exception("Error while indexing project")
           
        if not is_inserted:
            return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.INSERT_INTO_VECTORDB_ERROR.value,
                 "inserted_items_count":inserted_items_count
            }
        )
        
        

    return JSONResponse(
            content={
                "signal": ResponseSignal.INSERT_INTO_VECTORDB_SUCCESS.value,
                "inserted_items_count":inserted_items_count
            }
        )


@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request:Request ,project_id :str):
    project_model =await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
    
    project =await project_model.get_project_or_create_one(
        Project_id=project_id
    )

    nlp_controller =NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    collection_info =nlp_controller.get_vector_db_collection_info(project=project)

    return JSONResponse(
                content={
                    "signal": ResponseSignal.VECTORDB_COLLECTION_RETRIEVED.value,
                    "inserted_items_count":collection_info
                }
            )

@nlp_router.post("/index/search/{project_id}")
async def search_index(request:Request,project_id:str,search_rquest :SearchRequest):
    project_model =await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
    
    project =await project_model.get_project_or_create_one(
        Project_id=project_id
    )

    nlp_controller =NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    result =nlp_controller.search_vector_db_collection(project=project ,text=search_rquest.text,limit=search_rquest.limit)
    if not result:
        return  JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.VECTORDB_SEARCH_ERROR.value,
                    }
                )
    return JSONResponse(
        content={
             "signal": ResponseSignal.VECTORDB_SEARCH_SUCCESS.value,
             "result": [ res.dict()  for res in result ]
                }
         )


@nlp_router.post("/index/answer/{project_id}")
async def search_index(request:Request,project_id:str,search_rquest :SearchRequest):
    project_model =await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
    
    project =await project_model.get_project_or_create_one(
        Project_id=project_id
    )

    nlp_controller =NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
    )

    answer,full_prompt,chat_histor=nlp_controller.answer_rag_questions(
        project=project,
        query=search_rquest.text,
        limit=search_rquest.limit
    )

    if not answer:
        return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "signal": ResponseSignal.RAG_ANSWER_ERROR.value,
                    }
                )
    return JSONResponse(
        content={
            # "signal": ResponseSignal.RAG_ANSWER_SUCCESS.value,
             "answer":answer,
             #"full_prompt":full_prompt,
             #"chat_history":chat_histor
                }
         )



