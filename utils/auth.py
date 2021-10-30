import jwt
from decouple import config

def decode_token(token) -> dict | None: 
    try: 
        jwt_token = config('JWT_TOKEN')
        data = jwt.decode(token, jwt_token, algorithms=["HS256"])
        return data
    except Exception: 
        return None