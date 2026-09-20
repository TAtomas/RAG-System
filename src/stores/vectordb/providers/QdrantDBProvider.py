from qdrant_client import models ,QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from typing import List
import logging


class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_path :str,distance_method:str):

        self.client =None
        self.db_path=db_path

        if distance_method == DistanceMethodEnums.COSINE.value:
            distance_method=models.Distance.COSINE

        if distance_method == DistanceMethodEnums.DOT.value:
            distance_method=models.Distance.DOT

        self.logger= logging.getLogger(__file__)


    def connect(self):
        self.client=QdrantClient(path=self.db_path)

    def disconnect(self):
        self.client=None

    def is_collection_existed(self , collection_name :str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    def list_all_collections(self)->List :
        return self.client.get_collections()

    def get_collections_info(self,collection_name :str) ->dict :
        return self.client.get_collection(collection_name=collection_name)

    def delete_collection(self,collection_name:str):
        if self.is_collection_existed(collection_name=collection_name):
            return self.client.delete_collection(collection_name=collection_name)

    def create_collection(self ,collection_name:str , embedding_size:int ,do_rest :bool =False):

        if do_rest==True :
            _=self.delete_collection(collection_name=collection_name)
        if not self.is_collection_existed(collection_name=collection_name):
            _=self.client.creat_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=embedding_size,
                        distance=self.distance_method
                        )
                    )
            return True
        
        return False

    def insert_one(self ,collection_name :str ,text:str , vector:list ,metadeta:dict =None ,record_id:str =None):
        if not self.is_collection_existed(collection_name=collection_name):
            self.logger.error("Non exists Collection")
            return False 
        try:
            _=self.client.upload_records(
                collection_name=collection_name,
                records=[
                    models.record(
                        vector =vector,
                        pyload={
                            "text":text,
                            "metadeta":metadeta
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"error while insert record {e}")
            return False
        return True

    def insert_many(self ,collection_name :str ,texts:list , vectors:list ,metadeta:list =None ,record_ids:list =None,batch_size:int =50):
        if not self.is_collection_existed(collection_name=collection_name):
            self.logger.error("Non exists Collection")
            return False 
        if metadeta is None:
            metadeta = [None]*len(texts)

        for i in range(len(texts),batch_size):
            batch_end = i + batch_size
            batch_text = texts[i:batch_end]
            batch_vector =vectors[i:batch_end]
            batch_metadeta =metadeta[i:batch_end]

            batch_records=[
                models.record(
                    vector =batch_vector[x],
                    pyload ={
                        "text":batch_text[x],
                        "metadata":batch_metadeta[x]
                            }
                        )
                    for x in range(batch_size)
                  ]
        try:
            _=self.client.upload_records(
                collection_name=collection_name,
                records=batch_records
            )
        except Exception as e:
            self.logger.error(f"error while insert batch {e}")
            return False
        
        return True 


    def search_by_vector(self,collection_name:str,vector :list,limit:int=5):
        self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )




        






