import json
import jwt
from decouple import config
from modules.genesis.genesis_service import GenesisService

class AuthService: 
    def __init__(self): 
        self.genesis_service = GenesisService()

    def login(self, email, password): 
        [ genesisToken, userId, access ] = self.genesis_service.get_access_token(email, password)
        data = { "token": genesisToken, "userId": userId }
        accessToken = self.create_token(data)
        response = { "accessToken": accessToken, "access": access }
        return json.dumps(response)
    
    def create_token(self, data): 
        jwt_token = config('JWT_TOKEN')
        access_token = jwt.encode(data, jwt_token, algorithm="HS256")
        return access_token
