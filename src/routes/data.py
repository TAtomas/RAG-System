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
from models.AssetModel import AssetModel
from models.db_schemas.data_chunk import DataChunk
from models.db_schemas import Asset
from models.enums.AssetTypeEnum import AssetTypeEnum
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

    asset_model =await AssetModel.create_instance(
        db_client=request.app.db_client
    )

    asset_resourse =Asset(
        asset_project_id=project.id,
        asset_type=AssetTypeEnum.FILE,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )
    asset_recort=await asset_model.create_asset(asset=asset_resourse)


    return JSONResponse(
        {
          "content": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
          "file_id": str(asset_recort.id),
        }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(request:Request,project_id :str , ProcessRequest:ProcessRequest):
    #file_id =ProcessRequest.file_id
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

    project_files_ids={}
    asset_model =await AssetModel.create_instance(
                db_client=request.app.db_client
                )
    if ProcessRequest.file_id:
        asset_record=await asset_model.get_asset_record(
           asset_project_id=project.id,
           asset_name=ProcessRequest.file_id
        )
        if asset_record is None:
           return JSONResponse(
            status_code =status.HTTP_400_BAD_REQUEST,
            content={
                "signal":ResponseSignal.FILE_ID_ERROR.value
            }
            )
       
        project_files_ids= {
           asset_record.id:asset_record.asset_name
         }
           
    else:
        project_files =await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value
            )
        project_files_ids={
            record.id:record.asset_name
            for record in project_files
        }
        if len(project_files_ids) == 0 :
            return JSONResponse(
                        status_code =status.HTTP_400_BAD_REQUEST,
                        content={
                            "signal":ResponseSignal.NO_FILES_ERROR.value
                        }
                    )

    processed_records=0 
    processed_files=0

    chunk_model=await ChunkModel.create_instance(
            db_client=request.app.db_client
                    )
    
    if do_reset ==1 :
        _=await chunk_model.delete_chunks_by_project_id(
                 project_id=project.id
                )
    for asset_id,file_id in project_files_ids.items():
        file_content = processcontroller.get_file_content(file_id=file_id)

        if file_content ==None:
            logger.error(f"error while processing file id {file_id}")
            continue

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
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]
        

        processed_records += await chunk_model.insert_many_chunks(chunks=file_chunks_record)
        processed_files +=1
    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": processed_records,
            "processed_files":processed_files
        }
    )


    
        
   



                      