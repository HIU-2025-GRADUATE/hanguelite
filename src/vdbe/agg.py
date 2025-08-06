from src.util import *

class AggElem:
  def __init__(self, zKey: str, nMem: int):
      self.zKey: str = zKey
      self.pHash: AggElem = None  
      self.pNext: AggElem = None  
      self.aMem: list = [None] * nMem

class Agg:
  def __init__(self):
    self.nMem: int = 0
    self.pCurrent: AggElem = None
    self.nElem: int = 0
    self.nHash: int = 0
    self.apHash: list[AggElem] = []
    self.pFirst: AggElem = None
  
  def reset(self):
    self.nMem = 0
    self.pCurrent = None
    self.nElem = 0
    self.nHash = 0
    self.apHash.clear()
    self.pFirst = None

  def enhash(self, pElem: AggElem):
    h = hashNoCase(pElem.zKey, 0) % self.nHash
    pElem.pHash = self.apHash[h]
    self.apHash[h] = pElem

  def rehash(self, nHash: int):
    if self.nHash == nHash:
      return
    self.apHash = [None]*nHash
    self.nHash = nHash
    pElem = self.pFirst
    while pElem:
      self.enhash(pElem)
      pElem = pElem.pNext

  def insert(self, zKey: str):
    if self.nHash <= self.nElem * 2:
      self.rehash(self.nElem*2 + 19)
    if self.nHash == 0: 
      return 1
    
    pElem = AggElem(zKey, self.nMem)
    self.enhash(pElem)

    pElem.pNext = self.pFirst
    self.pFirst = pElem
    self.pCurrent = pElem
    self.nElem += 1

    return 0
  
  def aggInFocus(self):
    if self.pCurrent:
      return self.pCurrent
    
    pFocus = self.pFirst
    if pFocus:
      self.pCurrent = pFocus
    else:
      self.insert("")
      pFocus = self.pCurrent = self.pFirst

    return pFocus