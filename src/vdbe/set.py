from src.util import *

class SetElem:
    def __init__(self, zKey: str):
        self.pHash:SetElem = None  
        self.pNext:SetElem = None  
        self.zKey:str = zKey   

class Set:
    def __init__(self):
        self.pAll:SetElem = None               
        self.apHash:list[SetElem] = [None] * 41 

    def setInsert(self, zKey: str):
      h = hashNoCase(zKey, len(zKey)) % len(self.apHash)
      pElem = self.apHash[h]
      while pElem:
        if pElem.zKey == zKey:
          return
        pElem = pElem.pHash
      
      pElem = SetElem(zKey)
      pElem.pNext = self.pAll
      self.pAll = pElem
      pElem.pHash = self.apHash[h]
      self.apHash[h] = pElem

    def setTest(self, zKey: str):
      h = hashNoCase(zKey, len(zKey)) % len(self.apHash)
      pElem = self.apHash[h]
      while pElem:
        if pElem.zKey == zKey:
          return True
        pElem = pElem.pHash
      return False
