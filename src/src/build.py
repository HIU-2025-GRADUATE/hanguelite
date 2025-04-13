from sqliteInt import *
from util import *

# 원형 : sqliteExec
def exec(pParse : Parse):
    if pParse.pVdbe:
        if pParse.explain:
            # sqliteVdbeList(pParse.pVdbe, pParse.xCallback, pParse.pArg, pParse.zErrMsg)
            pass
        else:
            # trace = sys.stderr if (pParse.db.flags & SQLITE_VdbeTrace) != 0 else None
            # sqliteVdbeTrace(pParse.pVdbe, trace)
            pParse.pVdbe.exec(
                pParse.xCallback,
                pParse.pArg,
                pParse.zErrMsg,
                pParse.db.pBusyArg,
                pParse.db.xBusyCallback
            )
        pParse.pVdbe.delete()
        pParse.pVdbe = None
        pParse.colNamesSet = False

def findTable(db : sqlite, zName : str):
    h = hashNoCase(zName, 0) % N_HASH
    pTable = db.apTblHash[h]

    while pTable:
        if pTable.zName == zName:
            return pTable
        pTable = pTable.pHash

    return None