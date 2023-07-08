import jwt
from config.config import config


def decode_token(token):
    try:
        jwt_token = config["jwt"]["token"]
        data = jwt.decode(token, jwt_token, algorithms=["HS256"])
        return data
    except Exception:
        return None
