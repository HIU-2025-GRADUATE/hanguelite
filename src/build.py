from sqliteInt import *
from util import *


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

def sqliteExpr(op : int, pLeft : Expr, pRight : Expr, pToken : Token):
    if pToken:
        pNew = Expr(op, pLeft, pRight, pToken)
    else:
        pNew = Expr(op, pLeft, pRight, Token())

    if pLeft and pRight:
        sqliteExprSpan(pNew, pLeft.span, pRight.span)
    else:
        pNew.span = pNew.token

    return pNew

def sqliteExprSpan(pExpr : Expr, pLeft : Token, pRight : Token): #TODO 포인터 계산 처리 방법 고안
    pExpr.span.z = pLeft.z
    # pExpr.span.n = len(pRight.z) + (get_char_offset(pRight.z) - get_char_offset(pLeft.z))

def sqliteIdListAppend(pList : IdList, pToken : Token):
    resultList = pList or IdList()

    resultList.a.append(IdListItem())  # 기본값으로 새 IdItem 추가

    if pToken:
        resultList.a[resultList.nId].zName = pToken.z[:pToken.n].strip()

    resultList.nId += 1
    return resultList

def sqliteExprListAppend(pList : ExprList, pExpr : Expr, pName : Token):
    resultList = pList or ExprList()

    item = ExprListItem()
    item.pExpr = pExpr
    item.zName = ""

    if pName:
        item.zName = pName.z[:pName.n].strip()

    resultList.a.append(item)
    resultList.nExpr += 1

    return resultList

def sqliteFindTable(db : sqlite, zName : str):
    h = sqliteHashNoCase(zName, 0) % N_HASH
    pTable = db.apTblHash[h]

    while pTable:
        if pTable.zName == zName:
            return pTable
        pTable = pTable.pHash

    return None