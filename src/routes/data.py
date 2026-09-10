from fastapi import FastAPI,APIRouter,Depends,UploadFile,status
from fastapi.responses import JSONResponse
import aiofiles
import os
from helpers.config import get_settings,Settings
from controllers import DataController , ProjectController , ProcessController
from models import ResponseSignal
from .schemas.data import ProcessRequest
import logging

logger = logging.getLogger('uvicorn.error')

data_router =APIRouter(
    prefix ="/api/v1/data",
    tags =["api_vi","data"]
)

@data_router.post("/upload/{project_id}")
async def upload_data(project_id , file :UploadFile ,
                      app_settings : Settings = Depends(get_settings)):

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
          "file_id": file_id
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(project_id :str , ProcessRequest:ProcessRequest):
    file_id =ProcessRequest.file_id
    chunk_size =ProcessRequest.chunk_size
    overlap_size=ProcessRequest.overlap_size

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
    
    return file_chunks

    
        
   



                      