"""Provides some helpers for interacting with the database"""
import os

import pymongo
import pymongo.collection

_LOOKUP = {}


def get_client() -> pymongo.MongoClient:
    conn_str = os.environ.get('MONGO_CONNECTION', 'mongodb://localhost:27017')

    if conn_str not in _LOOKUP:
        _LOOKUP[conn_str] = pymongo.MongoClient(conn_str)

    return _LOOKUP[conn_str]


def get_collection(db_name: str, col_name: str) -> pymongo.collection.Collection:
    client = get_client()
    return client[db_name][col_name]
