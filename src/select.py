from sqliteInt import *
from tokenToConstant import *

def sqliteSelectNew(pEList, pSrc, pWhere, pGroupBy, pHaving, pOrderBy, isDistinct):
    pNew = Select()
    if pNew is None:
        return None  # 메모리 할당 실패 (파이썬에서는 필요 없지만 C 코드와 구조를 맞춤)

    pNew.pEList = pEList
    pNew.pSrc = pSrc
    pNew.pWhere = pWhere
    pNew.pGroupBy = pGroupBy
    pNew.pHaving = pHaving
    pNew.pOrderBy = pOrderBy
    pNew.isDistinct = isDistinct
    pNew.op = TK_SELECT 
    return pNew

def sqliteSelectDelete(p):
  if p is None:
     return
  del p

def sqliteParseInfoReset(pParse):
  pParse.aAgg = 0
  pParse.nAgg = 0
  pParse.iAggCount = -1
  pParse.useAgg = 0

def fillInColumnList(pParse, p):
  pTabList = p.pSrc;
  pEList = p.pEList;

  for i in range(pTabList.nid):
    if pTabList.a[i].pTab != None:
      return 0
    
    pTabList.a[i].pTab = sqliteFindTable(pParse.db, pTabList.a[i].zName);  # build.c 파일에 구현된 함수
    if pTabList.a[i].pTab == None: 
      sqliteSetString(&pParse.zErrMsg, "no such table: ", .a[i].zName, 0);
      pParse.nErr += 1
      return 1
    
  if pEList== None :
    for i in range(pTabList.nid):
      pTab = pTabList.a[i].pTab;
      for j in range(pTab.nCol):
        pExpr = sqliteExpr(TK_DOT, 0, 0, 0);
        pExpr.pLeft = sqliteExpr(TK_ID, 0, 0, 0);
        pExpr.pLeft.token.z = pTab.zName;
        pExpr.pLeft.token.n = len(pTab.zName);
        pExpr.pRight = sqliteExpr(TK_ID, 0, 0, 0);
        pExpr.pRight.token.z = pTab.aCol[j].zName;
        pExpr.pRight.token.n = len(pTab.aCol[j].zName);
        pExpr.span.z = "";
        pExpr.span.n = 0;
        pEList = sqliteExprListAppend(pEList, pExpr, 0);
      
    
    p.pEList = pEList;
  
  return 0

# opcode 상수로 치환 필요
def generateColumnNames(pParse, pTabList, pEList):
    v = pParse.pVdbe  

    if pParse.colNamesSet:
        return
    pParse.colNamesSet = 1

    sqliteVdbeAddOp(v, "OP_ColumnCount", pEList.nExpr, 0, 0, 0)

    for i in range(pEList.nExpr):
        p = None
        addr = None

        if pEList.a[i].zName:
            zName = pEList.a[i].zName
            sqliteVdbeAddOp(v, "OP_ColumnName", i, 0, zName, 0)
            continue

        p = pEList.a[i].pExpr

        if p.span.z and p.span.z[0]:
            addr = sqliteVdbeAddOp(v, "OP_ColumnName", i, 0, 0, 0)
            sqliteVdbeChangeP3(v, addr, p.span.z, p.span.n)
            sqliteVdbeCompressSpace(v, addr)

        elif p.op != TK_COLUMN or pTabList == None:
            zName = f"column{i + 1}"  # sprintf 대체
            sqliteVdbeAddOp(v, "OP_ColumnName", i, 0, zName, 0)

        else:
            if pTabList.nId > 1:
                zName = None
                pTab = pTabList.a[p.iTable].pTab
                zTab = pTabList.a[p.iTable].zAlias

                if zTab == None:
                    zTab = pTab.zName

                sqliteSetString(&zName, zTab, ".", pTab->aCol[p->iColumn].zName, 0);
                sqliteVdbeAddOp(v, "OP_ColumnName", i, 0, zName, 0)

            else:
                pTab = pTabList.a[0].pTab
                zName = pTab.aCol[p.iColumn].zName
                sqliteVdbeAddOp(v, "OP_ColumnName", i, 0, zName, 0)

# opcode 상수로 치환 필요
def selectInnerLoop(pParse, pEList, srcTab, nColumn, pOrderBy, distinct, eDest, iParm, iContinue, iBreak):
    v = pParse.pVdbe  # 포인터 참조 -> 점(.)으로 변경

    # Pull the requested columns.
    if pEList:
        for i in range(pEList.nExpr):
            sqliteExprCode(pParse, pEList.a[i].pExpr)
        nColumn = pEList.nExpr
    else:
        for i in range(nColumn):
            sqliteVdbeAddOp(v, "OP_Field", srcTab, i, 0, 0)

    sqliteVdbeAddOp(v, "OP_Callback", nColumn, 0, 0, 0)

    return 0
    

#sqliteWhereBegin
#sqliteWhereEnd

#sqliteExprResolveInSelect
#sqliteExprResolveIds
#sqliteExprCheck

#sqliteVdbeCreate
#sqliteVdbeAddOp