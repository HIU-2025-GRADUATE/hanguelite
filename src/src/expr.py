from sqliteInt import *

def exprResolveInSelect(pParse : Parse, pExpr : Expr):
    if pExpr is None:
        return

    if pExpr.op == TK_IN and pExpr.pSelect:
        pExpr.iTable = pParse.nTab
        pParse.nTab += 1
    else:
        if pExpr.pLeft:
            exprResolveInSelect(pParse, pExpr.pLeft)
        if pExpr.pRight:
            exprResolveInSelect(pParse, pExpr.pRight)
        if pExpr.pList:
            for expr_item in pExpr.pList.a:
                exprResolveInSelect(pParse, expr_item.pExpr)

def exprResolveIds(pParse : Parse, pTabList : IdList, pExpr : Expr):
    if pExpr is None:
        return 0

    if pExpr.op == TK_ID:
        cnt = 0
        # z = sqliteStrNDup(pExpr.token.z, pExpr.token.n)
        # for i in range(pTabList.nId):
        #     pTab = pTabList.a[i].pTab
        #     if pTab is None:
        #         continue
        #     for j in range(pTab.nCol):
        #         if sqliteStrICmp(pTab.aCol[j].zName, z) == 0:
        #             cnt += 1
        #             pExpr.iTable = i + pParse.nTab
        #             pExpr.iColumn = j
        # sqliteFree(z)
        # if cnt == 0:
        #     sqliteSetNString(pParse, "zErrMsg", "no such column: ", -1,
        #                      pExpr.token.z, pExpr.token.n, 0)
        #     pParse.nErr += 1
        #     return 1
        # elif cnt > 1:
        #     sqliteSetNString(pParse, "zErrMsg", "ambiguous column name: ", -1,
        #                      pExpr.token.z, pExpr.token.n, 0)
        #     pParse.nErr += 1
        #     return 1
        # pExpr.op = TK_COLUMN

    elif pExpr.op == TK_DOT:
        cnt = 0
        pLeft = pExpr.pLeft
        pRight = pExpr.pRight
        assert pLeft and pLeft.op == TK_ID
        assert pRight and pRight.op == TK_ID

        zLeft = pLeft.token.z
        zRight = pRight.token.z
        for i in range(pTabList.nId):
            pTab = pTabList.a[i].pTab
            if pTab is None:
                continue
            zTab = pTabList.a[i].zAlias or pTab.zName
            if zTab != zLeft:
                continue
            for j in range(pTab.nCol):
                if pTab.aCol[j].zName == zRight:
                    cnt += 1
                    pExpr.iTable = i + pParse.nTab
                    pExpr.iColumn = j
        if cnt == 0:
            pParse.nErr += 1
            return 1
        elif cnt > 1:
            pParse.nErr += 1
            return 1
        pExpr.pLeft = None
        pExpr.pRight = None
        pExpr.op = TK_COLUMN

    # elif pExpr.op == TK_IN:
    #     v = sqliteGetVdbe(pParse)
    #     if v is None:
    #         return 1
    #     if sqliteExprResolveIds(pParse, pTabList, pExpr.pLeft):
    #         return 1
    #     if pExpr.pSelect:
    #         sqliteVdbeAddOp(v, OP_Open, pExpr.iTable, 1, 0, 0)
    #         sqliteSelect(pParse, pExpr.pSelect, SRT_Set, pExpr.iTable)
    #     elif pExpr.pList:
    #         for e in pExpr.pList.a:
    #             if not isConstant(e.pExpr):
    #                 sqliteSetString(pParse, "zErrMsg",
    #                                 "right-hand side of IN operator must be constant", 0)
    #                 pParse.nErr += 1
    #                 return 1
    #             if sqliteExprCheck(pParse, e.pExpr, 0, 0):
    #                 return 1
    #         iSet = pExpr.iTable = pParse.nSet
    #         pParse.nSet += 1
    #         for e in pExpr.pList.a:
    #             pE2 = e.pExpr
    #             if pE2.op in (TK_FLOAT, TK_INTEGER, TK_STRING):
    #                 addr = sqliteVdbeAddOp(v, OP_SetInsert, iSet, 0, 0, 0)
    #                 sqliteVdbeChangeP3(v, addr, pE2.token.z, pE2.token.n)
    #                 sqliteVdbeDequoteP3(v, addr)
    #             else:
    #                 sqliteExprCode(pParse, pE2)
    #                 sqliteVdbeAddOp(v, OP_SetInsert, iSet, 0, 0, 0)

    # elif pExpr.op == TK_SELECT:
    #     pExpr.iColumn = pParse.nMem
    #     pParse.nMem += 1
    #     if sqliteSelect(pParse, pExpr.pSelect, SRT_Mem, pExpr.iColumn):
    #         return 1

    # else:
    #     if pExpr.pLeft and sqliteExprResolveIds(pParse, pTabList, pExpr.pLeft):
    #         return 1
    #     if pExpr.pRight and sqliteExprResolveIds(pParse, pTabList, pExpr.pRight):
    #         return 1
    #     if pExpr.pList:
    #         for e in pExpr.pList.a:
    #             if sqliteExprResolveIds(pParse, pTabList, e.pExpr):
    #                 return 1

    return 0

def exprCode(pParse : Parse, pExpr : Expr): #TODO : 추후에 제대로 함수 구현 필수
    v = pParse.pVdbe

    if pParse.useAgg:
        v.addOp(OP_AggGet, 0, pExpr.iAgg, 0, 0)
    else:
        v.addOp(OP_Field, pExpr.iTable, pExpr.iColumn, 0, 0)
      
