from sqliteInt import *


def sqliteExec(pParse):
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

def sqliteExpr(op, pLeft, pRight, pToken):
    pNew = Expr()
    if pNew is None:
        return None

    pNew.op = op
    pNew.pLeft = pLeft
    pNew.pRight = pRight

    if pToken is not None:
        pNew.token = pToken.copy()
    else:
        pNew.token = Token(z="", n=0)

    if pLeft is not None and pRight is not None:
        sqliteExprSpan(pNew, pLeft.span, pRight.span)
    else:
        pNew.span = pNew.token

    return pNew

def sqliteExprSpan(pExpr, pLeft, pRight): #TODO 포인터 계산 처리 방법 고안
    pExpr.span.z = pLeft.z
    # pExpr.span.n = len(pRight.z) + (get_char_offset(pRight.z) - get_char_offset(pLeft.z))

def sqliteIdListAppend(pList, pToken):
    if pList is None:
        pList = IdList()

    pList.a.append(IdListItem())  # 기본값으로 새 IdItem 추가

    if pToken is not None:
        pList.a[pList.nId].zName = pToken.z[:pToken.n].strip()

    pList.nId += 1
    return pList

def sqliteExprListAppend(pList, pExpr, pName):
    if pList is None:
        pList = ExprList()

    item = ExprListItem()
    item.pExpr = pExpr
    item.zName = None

    if pName is not None:
        item.zName = pName.z[:pName.n].strip()

    pList.a.append(item)
    pList.nExpr += 1

    return pList

def sqliteFindTable(db, zName):
    h = sqliteHashNoCase(zName, 0) % N_HASH
    pTable = db.apTblHash[h]

    while pTable is not None:
        if pTable.zName == zName:
            return pTable
        pTable = pTable.pHash

    return None
