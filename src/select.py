from src.where import *
from src.expr import *
from src.build import *
from src.tokenToConstant import *

def fillInColumnList(pParse : Parse, p : Select):
  pTabList = p.pSrc;
  pEList = p.pEList;

  for i in range(pTabList.nId):
    if pTabList.a[i].pTab:
      return 0
    
    # ================================= #
    # select * from tableA 쿼리가 정상 동작하도록 하는 코드
    # newTab = Table("tableA")
    # newTab.nCol = 6
    # newTab.aCol.append(Column("rowid"))
    # newTab.aCol.append(Column("학번"))
    # newTab.aCol.append(Column("이름"))
    # newTab.aCol.append(Column("학년"))
    # newTab.aCol.append(Column("전공"))
    # newTab.aCol.append(Column("전화번호"))
    # ================================= #
    pTabList.a[i].pTab = findTable(pParse.db, pTabList.a[i].zName);  # build.c 파일에 구현된 함수
    if pTabList.a[i].pTab == None: 
    #   sqliteSetString(&pParse.zErrMsg, "no such table: ", .a[i].zName, 0);
      pParse.nErr += 1
      return 1
    
  if pEList == None:
    for i in range(pTabList.nId):
      pTab = pTabList.a[i].pTab;
      for j in range(pTab.nCol):
        pExpr = Expr(TK_DOT, None, None, None);
        pExpr.pLeft = Expr(TK_ID, None, None, None);
        pExpr.pLeft.token.z = pTab.zName;
        pExpr.pLeft.token.n = len(pTab.zName);
        pExpr.pRight = Expr(TK_ID, None, None, None);
        pExpr.pRight.token.z = pTab.aCol[j].zName;
        pExpr.pRight.token.n = len(pTab.aCol[j].zName);
        pExpr.span.z = "";
        pExpr.span.n = 0;

        if pEList is None:
            pEList = ExprList()
        pEList.exprListAppend(pExpr, None);
      
    
    p.pEList = pEList;
  
  return 0

def generateColumnNames(pParse : Parse, pTabList : IdList, pEList : ExprList):
    v = pParse.pVdbe  

    if pParse.colNamesSet:
        return
    pParse.colNamesSet = 1

    v.addOp(OP_ColumnCount, pEList.nExpr, 0, 0, 0)

    for i in range(pEList.nExpr):
        if pEList.a[i].zName:
            zName = pEList.a[i].zName
            v.addOp(OP_ColumnName, i, 0, zName, 0)
            continue

        p = pEList.a[i].pExpr

        if p.span.z and p.span.z[0]:
            tmpStr = p.span.z[:p.span.n]
            tmpStr = ' '.join(tmpStr.split())
            v.addOp(OP_ColumnName, i, 0, tmpStr, 0)
            # sqliteVdbeChangeP3(v, addr, p.span.z, p.span.n)
            # sqliteVdbeCompressSpace(v, addr)

        elif p.op != TK_COLUMN or pTabList == None:
            zName = f"column{i + 1}"  # sprintf 대체
            v.addOp(OP_ColumnName, i, 0, zName, 0)

        else:
            if pTabList.nId > 1:
                pTab = pTabList.a[p.iTable].pTab
                zTab = pTabList.a[p.iTable].zAlias

                if zTab == None:
                    zTab = pTab.zName

                zName = zTab + "." + pTab.aCol[p.iColumn].zName
                v.addOp(OP_ColumnName, i, 0, zName, 0)

            else:
                pTab = pTabList.a[0].pTab
                zName = pTab.aCol[p.iColumn].zName
                v.addOp(OP_ColumnName, i, 0, zName, 0)

def selectInnerLoop(pParse : Parse, pEList : ExprList, srcTab : int, nColumn : int, pOrderBy : ExprList, 
                    distinct : int, eDest : int, iParm : int, iContinue : int, iBreak : int):
    v = pParse.pVdbe  

    if pEList:
        for i in range(pEList.nExpr):
            exprCode(pParse, pEList.a[i].pExpr)
        nColumn = pEList.nExpr
    else:
        for i in range(nColumn):
            v.addOp(OP_Field, srcTab, i, 0, 0)

    v.addOp(OP_Callback, nColumn, 0, 0, 0)

    return 0
    
def select(pParse : Parse, p : Select, eDest : int, iParm : int):
    isAgg = [0]
    distinct = -1

    pTabList = p.pSrc
    pWhere = p.pWhere
    pOrderBy = p.pOrderBy
    pGroupBy = p.pGroupBy
    pHaving = p.pHaving
    isDistinct = p.isDistinct

    base = pParse.nTab

    if pParse.nErr > 0:
        return 1

    pParse.infoReset()

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
        exprResolveInSelect(pParse, pEList.a[i].pExpr)

    if pWhere:
        exprResolveInSelect(pParse, pWhere)

    # if pOrderBy:
    #     for i in range(pOrderBy.nExpr):
    #         sqliteExprResolveInSelect(pParse, pOrderBy.a[i].pExpr)

    # if pGroupBy:
    #     for i in range(pGroupBy.nExpr):
    #         sqliteExprResolveInSelect(pParse, pGroupBy.a[i].pExpr)

    # if pHaving:
    #     sqliteExprResolveInSelect(pParse, pHaving)

    for i in range(pEList.nExpr):
        if exprResolveIds(pParse, pTabList, pEList.a[i].pExpr):
            return 1
        if exprCheck(pParse, pEList.a[i].pExpr, 1, isAgg):
            return 1

    if pWhere:
        if exprResolveIds(pParse, pTabList, pWhere):
            return 1
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

    if isAgg[0] == 1:
        assert pParse.nAgg == 0 and pParse.iAggCount < 0
        for i in range(pEList.nExpr):
            if exprAnalyzeAggregates(pParse, pEList.a[i].pExpr):
                return 1
        if pGroupBy:
            for i in range(pGroupBy.nExpr):
                if exprAnalyzeAggregates(pParse, pGroupBy.a[i].pExpr):
                    return 1
        # if pHaving and exprAnalyzeAggregates(pParse, pHaving):
        #     return 1
        # if pOrderBy:
        #     for i in range(pOrderBy.nExpr):
        #         if exprAnalyzeAggregates(pParse, pOrderBy.a[i].pExpr):
        #             return 1

    v = pParse.pVdbe

    if v is None:
        v = Vdbe(pParse.db.pBe)
        pParse.pVdbe = v
    # if v is None:
    #     pParse.zErrMsg = "out of memory"
    #     pParse.nErr += 1
    #     return 1

    # if pOrderBy:
    #     sqliteVdbeAddOp(v, OP_SortOpen, 0, 0, None, None)

    if eDest == SRT_Callback:
        generateColumnNames(pParse, pTabList, pEList)

    if isAgg[0] == 1:
        v.addOp(OP_AggReset, 0, pParse.nAgg, None, 0)

    # if eDest == SRT_Mem:
    #     sqliteVdbeAddOp(v, OP_Null, 0, 0, None, None)
    #     sqliteVdbeAddOp(v, OP_MemStore, iParm, 0, None, None)

    # if isDistinct:
    #     sqliteVdbeAddOp(v, OP_Open, distinct, 1, None, None)

    pWInfo = whereBegin(pParse, pTabList, pWhere, 0)
    if pWInfo is None:
        return 1

    if isAgg[0] == 0:
        if selectInnerLoop(pParse, pEList, 0, 0, pOrderBy, distinct, eDest, iParm,
                           pWInfo.iContinue, pWInfo.iBreak):
            return 1
        
    else:
        if pGroupBy:
            for i in range(pGroupBy.nExpr):
                exprCode(pParse, pGroupBy.a[i].pExpr)
            v.addOp(OP_MakeKey, pGroupBy.nExpr, 0, None, 0)
            doFocus = True
        else:
            doFocus = False
            for i in range(pParse.nAgg):
                if not pParse.aAgg[i].isAgg:
                    doFocus = True
                    break
            if doFocus:
                v.addOp(OP_String, 0, 0, "", 0)

        if doFocus:
            lbl1 = v.makeLabel()
            v.addOp(OP_AggFocus, 0, lbl1, None, 0)
            for i in range(pParse.nAgg):
                if pParse.aAgg[i].isAgg:
                    continue
                exprCode(pParse, pParse.aAgg[i].pExpr)
                v.addOp(OP_AggSet, 0, i, None, 0)
            v.resolveLabel(lbl1)

        for i in range(pParse.nAgg):
            if not pParse.aAgg[i].isAgg:
                continue
            pE = pParse.aAgg[i].pExpr
            if pE is None:
                v.addOp(OP_AggIncr, 1, i, None, 0)
                continue
            assert pE.op == TK_AGG_FUNCTION
            assert pE.pList is not None and pE.pList.nExpr == 1

            exprCode(pParse, pE.pList.a[0].pExpr)
            v.addOp(OP_AggGet, 0, i, None, 0)

            if pE.iColumn == FN_Min:
                op = OP_Min
            elif pE.iColumn == FN_Max:
                op = OP_Max
            elif pE.iColumn in (FN_Avg, FN_Sum):
                op = OP_Add

            v.addOp(op, 0, 0, None, 0)
            v.addOp(OP_AggSet, 0, i, None, 0)
    
    whereEnd(pWInfo)

    if isAgg[0] == 1:
        endagg = v.makeLabel()
        startagg = v.addOp(OP_AggNext, 0, endagg, None, 0)
        pParse.useAgg = 1

        # if pHaving:
        #     exprIfFalse(pParse, pHaving, startagg)

        if selectInnerLoop(pParse, pEList, 0, 0, pOrderBy, distinct, eDest, iParm,
                        startagg, endagg):
            return 1

        v.addOp(OP_Goto, 0, startagg, None, 0)
        v.addOp(OP_Noop, 0, 0, None, endagg)
        pParse.useAgg = 0

    pParse.nTab = base
    return 0