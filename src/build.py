from sqliteInt import *
from util import *

# 원형 : sqliteExec
def exec(pParse):
    if pParse.pVdbe:
        if pParse.explain:
            sqliteVdbeList(pParse.pVdbe, pParse.xCallback, pParse.pArg, pParse.zErrMsg)
        else:
            # trace = sys.stderr if (pParse.db.flags & SQLITE_VdbeTrace) != 0 else None
            # sqliteVdbeTrace(pParse.pVdbe, trace)
            sqliteVdbeExec(
                pParse.pVdbe,
                pParse.xCallback,
                pParse.pArg,
                pParse.zErrMsg,
                pParse.db.pBusyArg,
                pParse.db.xBusyCallback
            )
        sqliteVdbeDelete(pParse.pVdbe)
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