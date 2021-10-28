import json

from modules.genesis.genesis_service import GenesisService

class AuthService: 
    def __init__(self): 
        self.genesis_service = GenesisService()

    def login(self, email, password): 
        [ accessToken, userId ] = self.genesis_service.get_access_token(email, password)
        response = { "accessToken": accessToken, "userId": userId }
        return json.dumps(response)
    