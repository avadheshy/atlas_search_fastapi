import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from pymongo import MongoClient

app = FastAPI()
CLIENT = MongoClient('mongodb+srv://avadheshy2022:1997Avdy@cluster0.a2ic8ii.mongodb.net/test')
DB = CLIENT.SearchEngine


PAGE_SIZE = 20

@app.get("/find")
def find_products(search_term:str):
    result=DB["products"].aggregate([
      {"$search": {
        'index':'myindex',
          'compound': {
            'should': [
              {'autocomplete': {
                'query': search_term,
                'path': "name",
              }},
              {'exists': {
                'path': "manufacturer",
                'score': {
                  'boost': {
                    'value': 5
                  }
                }
              }}
            ]
          }
      }},
      {'$project':{
        '_id':0,
       }
       },
      {'$limit':10}
    ])
    return list(result)


@app.get("/search")
def list_students(search_term: str, page: str):
    """
    TODO: add products data
    """
    skip = (int(page) - 1) * PAGE_SIZE
    products = DB["products"].find({"$text": { "$search": search_term}}, {"_id": 0}).skip(skip).limit(PAGE_SIZE)
    return list(products)


