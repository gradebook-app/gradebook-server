import json

from modules.genesis.genesis_service import GenesisService

class GradesService: 
    def __init__(self): 
        self.genesisService = GenesisService()

    def grades(self, query, genesisId): 
        response = self.genesisService.get_grades(query, genesisId)
        return response
    
    def assignments(self, query, genesisId): 
        response = self.genesisService.get_assignments(query, genesisId)
        return { "assignments": response }