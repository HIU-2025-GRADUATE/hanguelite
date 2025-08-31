from src.util import *

class Sorter:
  def __init__(self):
    self.nKey = 0
    self.zKey : str
    self.nData = 0
    self.pData = 0
    self.pNext = 0

def Merge(pLeft: Sorter, pRight: Sorter):
  sHead = Sorter()
  pTail = sHead
  pTail.pNext = 0
  while pLeft != 0 and pRight != 0:
    c = sortCompare(pLeft.zKey, pRight.zKey)
    if c <= 0:
      pTail.pNext = pLeft
      pLeft = pLeft.pNext
    else:
      pTail.pNext = pRight
      pRight = pRight.pNext
    pTail = pTail.pNext
  
  if pLeft != 0:
    pTail.pNext = pLeft
  elif pRight != 0:
    pTail.pNext = pRight

  return sHead.pNext