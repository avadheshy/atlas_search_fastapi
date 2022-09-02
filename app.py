from calendar import day_abbr
from multiprocessing import managers
import os
from io import StringIO
from fastapi import FastAPI, Body, HTTPException, status, Query,File, UploadFile
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
from pymongo import MongoClient
import time
import csv
from io import BytesIO
import codecs


app = FastAPI()
CLIENT = MongoClient(
    'mongodb+srv://avadheshy2022:1997Avdy@cluster0.a2ic8ii.mongodb.net/test')
DB = CLIENT.SearchEngine
PAGE_SIZE = 20


def get_boosting_stage(search_term):
    # data = DB['boosting_config'].find_one({"active": True},{'_id':1})
    data = DB['product_booster'].find_one({'name':4}, {'_id': 0})
    print(data)
    boosting_stage = []
    for key, value in data.items():
        payload = {
            'autocomplete': {
                'query': search_term,
                'path': key,
                "score": {
                    "boost": {
                        "value": value
                    }
                }}}

        boosting_stage.append(payload)
    print(boosting_stage)
    return boosting_stage


def store_search_terms(user_id, search_term, search_results):
    DB['hst_search'].insert_one(
        {'user_id': user_id, 'search_term': search_term, 'search_results': search_results})
    return True


def store_autocomplete_results(user_id, search_term, search_results):
    DB['hst_autocomplete'].insert_one(
        {'user_id': user_id, 'search_term': search_term, 'search_results': search_results})
    return True


def get_autocomplete_pipeline(search_term, skip, limit):
    """
    This is autocomplete helper function
    """
    return [
        {
            '$search': {
                'index': 'myindex',
                'autocomplete': {
                    'path': 'name',
                    'query': search_term
                }
            }
        },
        {
            '$skip': skip
        },
        {
            '$limit': limit
        },
        {
            '$project': {
                '_id': 0,
                'name': 1,
                'product_id': 1
            }
        }
    ]


@app.post('/boost')
def add_booster(attribute_booster:dict):
    DB['product_booster'].insert_one(attribute_booster)
    return True
# @app.post('/boost')
# def add_booster(file: UploadFile = File(...)):
#     csvReader = csv.DictReader(codecs.iterdecode(file.file, 'unicode_escape'))
#     data = []
#     for row in csvReader:
#         data.append(row)

#     file.file.close()
#     DB['csv_booster'].insert_many(data)
#     return True
    


@app.get("/search")
def product_search(search_term: str, page: str):
    """
    Product Search API, This will help to discover the relevant products
    """
    
    st = time.time()
    boosting_data = get_boosting_stage(search_term)
    user_id = 1
    skip = (int(page) - 1) * PAGE_SIZE
    products = list(DB["products"].aggregate([
                    {"$search": {
                        'index': 'myindex',
                        'compound': {
                            'must': boosting_data
                        }
                    }},
                    {
                        '$project': {
                            '_id': 0,
                        }},
                    {"$skip": skip},
                    {'$limit': PAGE_SIZE}
                    ]))
    store_search_terms(user_id, search_term, products)
    et = time.time()

    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds')
    return products


@app.get("/autocomplete")
def search_autocomplete(search_term: str, page: str):
    """
    This API helps to auto complete the searched term
    """
    user_id = 1
    skip = (int(page) - 1) * PAGE_SIZE
    pipeline = get_autocomplete_pipeline(search_term, skip, PAGE_SIZE)
    products = list(DB["products"].aggregate(pipeline))
    store_autocomplete_results(user_id, search_term, products)
    return products


@app.get("/filter_category")
def filter_product(name:Optional[str]=None,year:Optional[str]=None,fuel:Optional[str]=None,seats:Optional[str]=None,min_price:Optional[str]=None,max_price:Optional[str]=None):
    filter_query = {}
    price_query={}
    if name:
        filter_query['name'] = name
    if year:
        filter_query['year'] = year
    if fuel:
        filter_query['fuel']=fuel
    if seats:
        filter_query['seats']=seats
    if min_price:
        price_query['$gte']= int(min_price)
                
    if max_price:
        price_query['$lt']= int(max_price)
    if len(price_query)>0:
        filter_query['selling_price']=price_query
    print(filter_query)
    result = list(DB["car_data"].aggregate([
        {"$project": {
            "_id": 0,
            "name": 1,
            "year": 1,
            "selling_price": 1,
            "km_driven": 1,
            "fuel": 1,
            "seller_type": 1,
            "transmission": 1,
            "seats": 1,
            "selling_price": {"$toInt": "$selling_price"}
            }},
        {'$match':filter_query},
        {'$limit': PAGE_SIZE}

]))
    return result
