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
def find_products(name_term:str,manufacturer_term):
    result=DB["products"].aggregate([
      {"$search": {
        'index':'myindex',
          'compound': {
            'must': [
              {'text': {
                'query': name_term,
                'path': "name",
                 "score": {
                  "boost": {
                  "value": 5
                 }
             }
              }},
              {'text': {
                'query': manufacturer_term,
                'path': "manufacturer",
                 "score": {
                  "boost": {
                  "value": 3
               }
             }
              }}
            ]
          }
      }},
      {'$project':{
        '_id':0
       }
       },
      {'$limit':20},

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


