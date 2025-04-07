from sqliteInt import *
from where import *
from expr import *
from build import *
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
    #   sqliteSetString(&pParse.zErrMsg, "no such table: ", .a[i].zName, 0);
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

                zName = zTab + "." + pTab.aCol[p.iColumn].zName
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
    
def sqliteSelect(pParse, p, eDest, iParm):
    i = 0
    isAgg = 0
    distinct = -1

    # SELECT 문 내부 파트 추출
    pTabList = p.pSrc
    pWhere = p.pWhere
    pOrderBy = p.pOrderBy
    pGroupBy = p.pGroupBy
    pHaving = p.pHaving
    isDistinct = p.isDistinct

    base = pParse.nTab

    if pParse.nErr > 0:
        return 1

    sqliteParseInfoReset(pParse)

    if fillInColumnList(pParse, p):
        return 1

    pEList = p.pEList

    if isDistinct:
        distinct = pParse.nTab
        pParse.nTab += 1

    if (eDest in [SRT_Mem, SRT_Set]) and pEList.nExpr > 1:
        pParse.zErrMsg = "only a single result allowed for a SELECT that is part of an expression"
        pParse.nErr += 1
        return 1

    if eDest != SRT_Callback:
        pOrderBy = None

    for i in range(pEList.nExpr):
        sqliteExprResolveInSelect(pParse, pEList.a[i].pExpr)

    # if pWhere:
    #     sqliteExprResolveInSelect(pParse, pWhere)

    # if pOrderBy:
    #     for i in range(pOrderBy.nExpr):
    #         sqliteExprResolveInSelect(pParse, pOrderBy.a[i].pExpr)

    # if pGroupBy:
    #     for i in range(pGroupBy.nExpr):
    #         sqliteExprResolveInSelect(pParse, pGroupBy.a[i].pExpr)

    # if pHaving:
    #     sqliteExprResolveInSelect(pParse, pHaving)

    for i in range(pEList.nExpr):
        if sqliteExprResolveIds(pParse, pTabList, pEList.a[i].pExpr):
            return 1
        # if sqliteExprCheck(pParse, pEList.a[i].pExpr, 1, isAgg):
        #     return 1

    # if pWhere:
    #     if sqliteExprResolveIds(pParse, pTabList, pWhere):
    #         return 1
    #     if sqliteExprCheck(pParse, pWhere, 0, None):
    #         return 1

    # if pOrderBy:
    #     for i in range(pOrderBy.nExpr):
    #         pE = pOrderBy.a[i].pExpr
    #         if sqliteExprResolveIds(pParse, pTabList, pE):
    #             return 1
    #         if sqliteExprCheck(pParse, pE, isAgg, None):
    #             return 1

    # if pGroupBy:
    #     for i in range(pGroupBy.nExpr):
    #         pE = pGroupBy.a[i].pExpr
    #         if sqliteExprResolveIds(pParse, pTabList, pE):
    #             return 1
    #         if sqliteExprCheck(pParse, pE, isAgg, None):
    #             return 1

    # if pHaving:
    #     if not pGroupBy:
    #         pParse.zErrMsg = "a GROUP BY clause is required before HAVING"
    #         pParse.nErr += 1
    #         return 1
    #     if sqliteExprResolveIds(pParse, pTabList, pHaving):
    #         return 1
    #     if sqliteExprCheck(pParse, pHaving, isAgg, None):
    #         return 1

    # if isAgg:
    #     assert pParse.nAgg == 0 and pParse.iAggCount < 0
    #     for i in range(pEList.nExpr):
    #         if sqliteExprAnalyzeAggregates(pParse, pEList.a[i].pExpr):
    #             return 1
    #     if pGroupBy:
    #         for i in range(pGroupBy.nExpr):
    #             if sqliteExprAnalyzeAggregates(pParse, pGroupBy.a[i].pExpr):
    #                 return 1
    #     if pHaving and sqliteExprAnalyzeAggregates(pParse, pHaving):
    #         return 1
    #     if pOrderBy:
    #         for i in range(pOrderBy.nExpr):
    #             if sqliteExprAnalyzeAggregates(pParse, pOrderBy.a[i].pExpr):
    #                 return 1

    v = pParse.pVdbe

    if v is None:
        v = sqliteVdbeCreate(pParse.db.pBe)
        pParse.pVdbe = v
    if v is None:
        pParse.zErrMsg = "out of memory"
        pParse.nErr += 1
        return 1

    # if pOrderBy:
    #     sqliteVdbeAddOp(v, OP_SortOpen, 0, 0, None, None)

    if eDest == SRT_Callback:
        generateColumnNames(pParse, pTabList, pEList)

    # if isAgg:
    #     sqliteVdbeAddOp(v, OP_AggReset, 0, pParse.nAgg, None, None)

    # if eDest == SRT_Mem:
    #     sqliteVdbeAddOp(v, OP_Null, 0, 0, None, None)
    #     sqliteVdbeAddOp(v, OP_MemStore, iParm, 0, None, None)

    # if isDistinct:
    #     sqliteVdbeAddOp(v, OP_Open, distinct, 1, None, None)

    pWInfo = sqliteWhereBegin(pParse, pTabList, pWhere, None)
    if pWInfo is None:
        return 1

    if not isAgg:
        if selectInnerLoop(pParse, pEList, None, None, pOrderBy, distinct, eDest, iParm,
                           pWInfo.iContinue, pWInfo.iBreak):
            return 1
    # else:
    #     doFocus = 0
    #     if pGroupBy:
    #         for i in range(pGroupBy.nExpr):
    #             sqliteExprCode(pParse, pGroupBy.a[i].pExpr)
    #         sqliteVdbeAddOp(v, OP_MakeKey, pGroupBy.nExpr, 0, None, None)
    #         doFocus = 1
    #     else:
    #         for i in range(pParse.nAgg):
    #             if not pParse.aAgg[i].isAgg:
    #                 doFocus = 1
    #                 break
    #         if doFocus:
    #             sqliteVdbeAddOp(v, OP_String, 0, 0, "", None)

    #     if doFocus:
    #         lbl1 = sqliteVdbeMakeLabel(v)
    #         sqliteVdbeAddOp(v, OP_AggFocus, 0, lbl1, None, None)
    #         for i in range(pParse.nAgg):
    #             if pParse.aAgg[i].isAgg:
    #                 continue
    #             sqliteExprCode(pParse, pParse.aAgg[i].pExpr)
    #             sqliteVdbeAddOp(v, OP_AggSet, 0, i, None, None)
    #         sqliteVdbeResolveLabel(v, lbl1)

    #     for i in range(pParse.nAgg):
    #         if not pParse.aAgg[i].isAgg:
    #             continue
    #         pE = pParse.aAgg[i].pExpr
    #         if pE is None:
    #             sqliteVdbeAddOp(v, OP_AggIncr, 1, i, None, None)
    #             continue
    #         assert pE.op == TK_AGG_FUNCTION
    #         assert pE.pList and pE.pList.nExpr == 1
    #         sqliteExprCode(pParse, pE.pList.a[0].pExpr)
    #         sqliteVdbeAddOp(v, OP_AggGet, 0, i, None, None)

    #         if pE.iColumn == FN_Min:
    #             op = OP_Min
    #         elif pE.iColumn == FN_Max:
    #             op = OP_Max
    #         elif pE.iColumn in [FN_Avg, FN_Sum]:
    #             op = OP_Add

    #         sqliteVdbeAddOp(v, op, 0, 0, None, None)
    #         sqliteVdbeAddOp(v, OP_AggSet, 0, i, None, None)

    sqliteWhereEnd(pWInfo)

    # if isAgg:
    #     endagg = sqliteVdbeMakeLabel(v)
    #     startagg = sqliteVdbeAddOp(v, OP_AggNext, 0, endagg, None, None)
    #     pParse.useAgg = 1
    #     if pHaving:
    #         sqliteExprIfFalse(pParse, pHaving, startagg)
    #     if selectInnerLoop(pParse, pEList, None, None, pOrderBy, distinct,
    #                        eDest, iParm, startagg, endagg):
    #         return 1
    #     sqliteVdbeAddOp(v, OP_Goto, 0, startagg, None, None)
    #     sqliteVdbeAddOp(v, OP_Noop, 0, 0, None, endagg)
    #     pParse.useAgg = 0

    # if pOrderBy:
    #     generateSortTail(v, pEList.nExpr)

    pParse.nTab = base
    return 0



#sqliteVdbeCreate
#sqliteVdbeAddOp