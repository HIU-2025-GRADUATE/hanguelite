from src.util import *

"""
/*
** A sorter builds a list of elements to be sorted.  Each element of
** the list is an instance of the following structure.
*/
"""

class Sorter:
    nKey: int       # /* Number of bytes in the key */
    zKey: str       # /* The key by which we will sort */
    nData: int      # /* Number of bytes in the data */
    pData: str      # /* The data associated with this key */
    pNext = 0       # /* Next in the list */

    def __del__(self):
        del self.nKey
        del self.zKey
        del self.nData
        del self.pData
        del self.pNext

# static Sorter *Merge(Sorter *pLeft, Sorter *pRight)
def Merge(pLeft: Sorter, pRight: Sorter):
    sHead = Sorter()
    pTail = sHead
    pTail.pNext = 0

    while pLeft and pRight:
        c = sortCompare(pLeft.zKey, pRight.zKey)

        if c <= 0:
            pTail.pNext = pLeft
            pLeft = pLeft.pNext
        else:
            pTail.pNext = pRight
            pRight = pRight.pNext

        pTail.pNext = pRight

    if pLeft:
        pTail.pNext = pLeft
    elif pRight:
        pTail.pNext = pRight

    return sHead.pNext
