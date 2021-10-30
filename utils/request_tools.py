from functools import wraps
from flask import request
import json
from utils.auth import decode_token

def body(f):
    @wraps(f)
    def body_handler(*args, **kwargs):
        body = json.loads(request.data.decode('utf-8'))
        return f(body, *args, **kwargs)
    return body_handler


def query(f): 
    @wraps(f)
    def query_handler(*args, **kwargs): 
        query = request.query_string
        try:
            query = { i.split("=")[0] : i.split("=")[1] for i in query.decode().split("&")}
        except Exception: 
            query = {}
            
        return f(*args, query, **kwargs)
    return query_handler

def genesisId(f): 
    @wraps(f)
    def handle_genesisId(*args, **kwargs): 
        accessToken = request.headers['Authorization'][7:].strip()
        decoded_data = decode_token(accessToken)
        if decode_token == None: 
            return {}
        return f(*args, decoded_data, **kwargs)
    return handle_genesisId