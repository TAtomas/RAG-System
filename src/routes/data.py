from fastapi import FastAPI,APIRouter,Depends,UploadFile,status ,Request
from fastapi.responses import JSONResponse
import aiofiles
import os
from helpers.config import get_settings,Settings
from controllers import DataController , ProjectController , ProcessController
from models import ResponseSignal
from .schemas.data import ProcessRequest
import logging
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemas.data_chunk import DataChunk
logger = logging.getLogger('uvicorn.error')

data_router =APIRouter(
    prefix ="/api/v1/data",
    tags =["api_vi","data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(request:Request,project_id , file :UploadFile ,
                      app_settings : Settings = Depends(get_settings)):

    project_model=await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    project =await project_model.get_project_or_create_one(
        Project_id=project_id
    )

    data_controller=DataController()
    is_valid , ruselt=data_controller.valildate_uploaded_file(file =file)
    if not is_valid:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUSET,
            content={
                "signal":ruselt
            }
        )
    project_dir_path = ProjectController().get_project_path(project_id=project_id)

    file_path , file_id  = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
        )
    try:

        async with aiofiles.open(file_path ,"wb") as f :
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk),

    except Exception as e :
        logger.error(f"error while uploading a file : {e}")
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUSET,
            content={
                "signal":ResponseSignal.FILE_UPLOAD_FAILED
            }

        )


    return JSONResponse(
        {
          "content": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
          "file_id": file_id,
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request:Request,project_id :str , ProcessRequest:ProcessRequest):
    file_id =ProcessRequest.file_id
    chunk_size =ProcessRequest.chunk_size
    overlap_size=ProcessRequest.overlap_size
    do_reset =ProcessRequest.do_reset
    
    project_model=await ProjectModel.create_instance(
            db_client=request.app.db_client
        )
    project =await project_model.get_project_or_create_one(
            Project_id=project_id
        )
    
    processcontroller = ProcessController(project_id=project_id)

    file_content = processcontroller.get_file_content(file_id=file_id)

    file_chunks = processcontroller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        overlap_size=overlap_size
    )

    if file_chunks is None or len(file_chunks)==0:
        return JSONResponse(
            status_code =status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.PROCESSING_FAILED.value
            }
        )
    
    file_chunks_record=[
          DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=project.id,
        )
         for i, chunk in enumerate(file_chunks)
    ]

    chunk_model=await ChunkModel.create_instance(
       db_client=request.app.db_client
            )
    
    if do_reset ==1 :
        _=await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )
    
    no_rec = await chunk_model.insert_many_chunks(chunks=file_chunks_record)

    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_rec
        }
    )


    
        
   



                      