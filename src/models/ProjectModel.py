from .BaseDataModel import BaseDataModel
from .db_schemas.project  import Project
from .enums.DatabaseEnum import DatabaseEnum


class ProjectModel(BaseDataModel):
    def __init__(self,db_client : object):
        super().__init__(db_client = db_client)
        self.collection =db_client[DatabaseEnum.COLLECTION_PROJECT_NAME.value]

    @classmethod
    async def create_instance(cls ,db_client : object):
        instance=cls(db_client)
        await instance.init_collection()
        return instance



    async def init_collection(self):
        all_collctions =await self.db_client.list_collection_names()
        if DatabaseEnum.COLLECTION_PROJECT_NAME.value not in all_collctions:
            self.collection =self.db_client[DatabaseEnum.COLLECTION_PROJECT_NAME.value]
            indexes =Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )





    async def create_project(self, Project : Project):

        result= await self.collection.insert_one(Project.dict(by_alias=True, exclude_unset=True))
        Project._id=result.inserted_id


        return Project

    async def get_project_or_create_one(self,Project_id : str):
        record = await self.collection.find_one(
            {
                "project_id":Project_id
            }
        )

        if record == None :
            project =Project(project_id=Project_id)
            project = await self.create_project(Project=project)
            return project

        return Project(**record)

    async def get_all_projects(self ,page : int =1 ,page_size: int =10):
        total_documents = await self.collection.count_documents({})

        total_pages = total_documents // page_size
        if total_documents % page_size> 0:
            total_pages+=1

        cursor = await self.collection.find().skip((page-1) * page_size).limit(page_size)

        projects =[]
        async for document in cursor:
            projects.append(
                Project(**document)
            )

        return projects,total_pages
            

        

        