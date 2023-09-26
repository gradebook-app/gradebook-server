from dataclasses import dataclass

@dataclass
class GeneralUserAccount(): 
    name: str
    studentId: str

@dataclass
class GeneralUserAccountRO(): 
    accounts: list[GeneralUserAccount]