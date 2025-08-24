from src.sqliteInt import *

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
        z = pExpr.token.z
        for i in range(pTabList.nId):
            pTab = pTabList.a[i].pTab
            if pTab is None:
                continue
            for j in range(pTab.nCol):
                if pTab.aCol[j].zName == z:
                    cnt += 1
                    pExpr.iTable = i + pParse.nTab
                    pExpr.iColumn = j
        if cnt == 0:
            raise ValueError(f"no such column: {pExpr.token.z}")
        elif cnt > 1:
            raise ValueError(f"ambiguous column name: {pExpr.token.z}")
        pExpr.op = TK_COLUMN

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

    elif pExpr.op == TK_IN:
        v = pParse.pVdbe
        if v is None:
            v = pParse.pVdbe = Vdbe(pParse.db.pBe)

        if exprResolveIds(pParse, pTabList, pExpr.pLeft):
            return 1
        
        # if pExpr.pSelect:
        #     v.addOp(OP_Open, pExpr.iTable, 1, None, 0)
        #     if select(pParse, pExpr.pSelect, SRT_Set, pExpr.iTable)
        if pExpr.pList:
            iSet = pExpr.iTable = pParse.nSet
            pParse.nSet += 1

            for i in range(pExpr.pList.nExpr):
                pE2 = pExpr.pList.a[i].pExpr
                if not isConstant(pE2):
                    # sqliteSetString(pParse.zErrMsg, "right-hand side of IN operator must be constant", None)
                    pParse.nErr += 1
                    return 1
                if exprCheck(pParse, pE2, 0, None):
                    return 1

            for i in range(pExpr.pList.nExpr):
                pE2 = pExpr.pList.a[i].pExpr
                if pE2.op in (TK_FLOAT, TK_INTEGER, TK_STRING):
                    addr = v.addOp(OP_SetInsert, iSet, 0, pE2.token.z, 0)
                    v.dequoteP3(addr)
                else:
                    exprCode(pParse, pE2)
                    v.addOp(OP_SetInsert, iSet, 0, None, 0)

    else:
        if pExpr.pLeft and exprResolveIds(pParse, pTabList, pExpr.pLeft):
            return 1
        if pExpr.pRight and exprResolveIds(pParse, pTabList, pExpr.pRight):
            return 1
        if pExpr.pList:
            for e in pExpr.pList.a:
                if exprResolveIds(pParse, pTabList, e.pExpr):
                    return 1

    return 0

def exprCode(pParse : Parse, pExpr : Expr): 
    v = pParse.pVdbe
    op = 0

    if pExpr.op == TK_AND:    
        op = OP_And
    elif pExpr.op == TK_OR:     
        op = OP_Or
    elif pExpr.op == TK_LT:     
        op = OP_Lt
    elif pExpr.op == TK_LE:     
        op = OP_Le
    elif pExpr.op == TK_GT:     
        op = OP_Gt
    elif pExpr.op == TK_GE:     
        op = OP_Ge
    elif pExpr.op == TK_NE:     
        op = OP_Ne
    elif pExpr.op == TK_EQ:     
        op = OP_Eq
    elif pExpr.op == TK_LIKE:   
        op = OP_Like
    elif pExpr.op == TK_NOT:   
        op = OP_Not        
    elif pExpr.op == TK_ISNULL:   
        op = OP_IsNull
    elif pExpr.op == TK_NOTNULL:   
        op = OP_NotNull 

    if pExpr.op == TK_COLUMN:
        if pParse.useAgg:
            v.addOp(OP_AggGet, 0, pExpr.iAgg, 0, 0)
        else:
            v.addOp(OP_Field, pExpr.iTable, pExpr.iColumn, 0, 0)

    elif pExpr.op == TK_INTEGER:
        val = int(pExpr.token.z)
        v.addOp(OP_Integer, val, 0, 0, 0)

    elif pExpr.op == TK_FLOAT:
        addr = v.addOp(OP_String, 0, 0, pExpr.token.z, 0)

    elif pExpr.op == TK_STRING:
        addr = v.addOp(OP_String, 0, 0, pExpr.token.z, 0)
        v.dequoteP3(addr)

    elif pExpr.op == TK_NULL:
        v.addOp(OP_Null, 0, 0, 0, 0)

    elif pExpr.op in (TK_AND, TK_OR, TK_STAR):
        exprCode(pParse, pExpr.pLeft)
        exprCode(pParse, pExpr.pRight)
        v.addOp(op, 0, 0, 0, 0)

    elif pExpr.op in (TK_LT, TK_LE, TK_GT, TK_GE, TK_NE, TK_EQ, TK_LIKE):
        v.addOp(OP_Integer, 1, 0, 0, 0)
        exprCode(pParse, pExpr.pLeft)
        exprCode(pParse, pExpr.pRight)
        dest = v.currentAddr() + 2
        v.addOp(op, 0, dest, 0, 0)
        v.addOp(OP_AddImm, -1, 0, 0, 0)

    elif pExpr.op == TK_NOT:
        exprCode(pParse, pExpr.pLeft)
        v.addOp(op, 0, 0, 0, 0)

    elif pExpr.op in (TK_ISNULL, TK_NOTNULL):
        v.addOp(OP_Integer, 1, 0, None, 0)
        exprCode(pParse, pExpr.pLeft)
        dest = v.currentAddr() + 2
        v.addOp(op, 0, dest, None, 0)
        v.addOp(OP_AddImm, -1, 0, None, 0)

    elif pExpr.op == TK_SELECT:
        v.addOp(OP_MemLoad, pExpr.iColumn, 0, 0, 0)

    elif pExpr.op == TK_AGG_FUNCTION:
        v.addOp(OP_AggGet, 0, pExpr.iAgg, None, 0)
        if pExpr.iColumn == FN_Avg:
            assert 0 <= pParse.iAggCount < pParse.nAgg
            v.addOp(OP_AggGet, 0, pParse.iAggCount, None, 0)
            v.addOp(OP_Divide, 0, 0, None, 0)

    elif pExpr.op == TK_FUNCTION:
        id = pExpr.iColumn
        pList = pExpr.pList

        if id == FN_Fcnt:
            v.addOp(OP_Fcnt, 0, 0, None, 0)
        else:
            op = OP_Min if id == FN_Min else OP_Max
            for i in range(pList.nExpr):
                exprCode(pParse, pList.a[i].pExpr)
                if i > 0:
                    v.addOp(op, 0, 0, None, 0)

    elif pExpr.op == TK_IN:
        v.addOp(OP_Integer, 1, 0, None, 0)
        exprCode(pParse, pExpr.pLeft)
        addr = v.currentAddr()
        if pExpr.pSelect:
            v.addOp(OP_Found, pExpr.iTable, addr + 2, None, 0)
        else:
            v.addOp(OP_SetFound, pExpr.iTable, addr + 2, None, 0)
        v.addOp(OP_AddImm, -1, 0, None, 0)

    elif pExpr.op == TK_BETWEEN:
        lbl = v.makeLabel()
        v.addOp(OP_Integer, 0, 0, None, 0)
        exprIfFalse(pParse, pExpr, lbl)
        v.addOp(OP_AddImm, 1, 0, None, 0)
        v.resolveLabel(lbl)

def exprIfTrue(pParse : Parse, pExpr : Expr, dest : int):
    v = pParse.pVdbe
    op = 0

    if pExpr.op == TK_LT:        
        op = OP_Lt
    elif pExpr.op == TK_LE:      
        op = OP_Le
    elif pExpr.op == TK_GT:      
        op = OP_Gt
    elif pExpr.op == TK_GE:      
        op = OP_Ge
    elif pExpr.op == TK_NE:      
        op = OP_Ne
    elif pExpr.op == TK_EQ:      
        op = OP_Eq
    elif pExpr.op == TK_LIKE:    
        op = OP_Like
    elif pExpr.op == TK_ISNULL:     
        op = OP_IsNull
    elif pExpr.op == TK_NOTNULL:   
        op = OP_NotNull

    if pExpr.op == TK_AND:
        d2 = v.makeLabel()
        exprIfFalse(pParse, pExpr.pLeft, d2)
        exprIfTrue(pParse, pExpr.pRight, dest)
        v.resolveLabel(d2)

    elif pExpr.op == TK_OR:
        exprIfTrue(pParse, pExpr.pLeft, dest)
        exprIfTrue(pParse, pExpr.pRight, dest)

    elif pExpr.op == TK_NOT:
        exprIfFalse(pParse, pExpr.pLeft, dest)

    elif pExpr.op in (TK_LT, TK_LE, TK_GT, TK_GE, TK_NE, TK_EQ, TK_LIKE):
        exprCode(pParse, pExpr.pLeft)
        exprCode(pParse, pExpr.pRight)
        v.addOp(op, 0, dest, 0, 0)

    elif pExpr.op in (TK_ISNULL, TK_NOTNULL):
        exprCode(pParse, pExpr.pLeft)
        v.addOp(op, 0, dest, None, 0)

    elif pExpr.op == TK_IN:
        exprCode(pParse, pExpr.pLeft)
        if pExpr.pSelect:
            v.addOp(OP_Found, pExpr.iTable, dest, None, 0)
        else:
            v.addOp(OP_SetFound, pExpr.iTable, dest, None, 0)

    elif pExpr.op == TK_BETWEEN:
        lbl = v.makeLabel()
        exprCode(pParse, pExpr.pLeft)
        v.addOp(OP_Dup, 0, 0, None, 0)
        exprCode(pParse, pExpr.pList.a[0].pExpr)
        v.addOp(OP_Lt, 0, lbl, None, 0)
        exprCode(pParse, pExpr.pList.a[1].pExpr)
        v.addOp(OP_Le, 0, dest, None, 0)
        v.addOp(OP_Integer, 0, 0, None, 0)
        v.addOp(OP_Pop, 1, 0, None, lbl)

    else:
        exprCode(pParse, pExpr)
        v.addOp(OP_If, 0, dest, None, 0)

def exprIfFalse(pParse : Parse, pExpr : Expr, dest : int):
    v = pParse.pVdbe
    op = 0

    if pExpr.op == TK_LT:       
        op = OP_Ge
    elif pExpr.op == TK_LE:     
        op = OP_Gt
    elif pExpr.op == TK_GT:     
        op = OP_Le
    elif pExpr.op == TK_GE:     
        op = OP_Lt
    elif pExpr.op == TK_NE:     
        op = OP_Eq
    elif pExpr.op == TK_EQ:     
        op = OP_Ne
    elif pExpr.op == TK_LIKE:   
        op = OP_Like
    elif pExpr.op == TK_ISNULL:     
        op = OP_NotNull
    elif pExpr.op == TK_NOTNULL:   
        op = OP_IsNull

    if pExpr.op == TK_AND:
        exprIfFalse(pParse, pExpr.pLeft, dest)
        exprIfFalse(pParse, pExpr.pRight, dest)

    elif pExpr.op == TK_OR:
        d2 = v.makeLabel()
        exprIfTrue(pParse, pExpr.pLeft, d2)
        exprIfFalse(pParse, pExpr.pRight, dest)
        v.resolveLabel(d2)

    elif pExpr.op == TK_NOT:
        exprIfTrue(pParse, pExpr.pLeft, dest)

    elif pExpr.op in (TK_LT, TK_LE, TK_GT, TK_GE, TK_NE, TK_EQ):
        exprCode(pParse, pExpr.pLeft)
        exprCode(pParse, pExpr.pRight)
        v.addOp(op, 0, dest, 0, 0)

    elif pExpr.op == TK_LIKE:
        exprCode(pParse, pExpr.pLeft)
        exprCode(pParse, pExpr.pRight)
        v.addOp(op, 1, dest, 0, 0)

    elif pExpr.op in (TK_ISNULL, TK_NOTNULL):
        exprCode(pParse, pExpr.pLeft)
        v.addOp(op, 0, dest, None, 0)

    elif pExpr.op == TK_IN:
        exprCode(pParse, pExpr.pLeft)
        if pExpr.pSelect:
            v.addOp(OP_NotFound, pExpr.iTable, dest, None, 0)
        else:
            v.addOp(OP_SetNotFound, pExpr.iTable, dest, None, 0)

    elif pExpr.op == TK_BETWEEN:
        exprCode(pParse, pExpr.pLeft)
        v.addOp(OP_Dup, 0, 0, None, 0)
        exprCode(pParse, pExpr.pList.a[0].pExpr)
        addr = v.currentAddr()
        v.addOp(OP_Ge, 0, addr + 3, None, 0)
        v.addOp(OP_Pop, 1, 0, None, 0)
        v.addOp(OP_Goto, 0, dest, None, 0)
        exprCode(pParse, pExpr.pList.a[1].pExpr)
        v.addOp(OP_Gt, 0, dest, None, 0)

    else:
        exprCode(pParse, pExpr)
        v.addOp(OP_Not, 0, 0, None, 0)
        v.addOp(OP_If, 0, dest, None, 0)

def exprCheck(pParse: Parse, pExpr: Expr, allowAgg: int, pIsAgg: list[int]):
    nErr = 0
    if pExpr is None:
        return 0

    if pExpr.op == TK_FUNCTION:
        id = funcId(pExpr.token)
        n = pExpr.pList.nExpr if pExpr.pList else 0
        noSuchFunc = False
        tooManyArgs = False
        tooFewArgs = False
        isAgg = False

        pExpr.iColumn = id

        if id == FN_Unknown:
            noSuchFunc = True
        elif id == FN_Count:
            noSuchFunc = not allowAgg
            tooManyArgs = n > 1
            isAgg = True
        elif id in (FN_Max, FN_Min):
            tooFewArgs = n < 1 if allowAgg else n < 2
            isAgg = (n == 1)
        elif id in (FN_Avg, FN_Sum):
            noSuchFunc = not allowAgg
            tooManyArgs = n > 1
            tooFewArgs = n < 1
            isAgg = True
        elif id == FN_Fcnt:
            n = 0
        

        if noSuchFunc:
            pParse.zErrMsg = f"no such function: {pExpr.token.z}"
            pParse.nErr += 1
            nErr += 1
        elif tooManyArgs:
            pParse.zErrMsg = f"too many arguments to function {pExpr.token.z}()"
            pParse.nErr += 1
            nErr += 1
        elif tooFewArgs:
            pParse.zErrMsg = f"too few arguments to function {pExpr.token.z}()"
            pParse.nErr += 1
            nErr += 1

        if isAgg:
            pExpr.op = TK_AGG_FUNCTION
            if pIsAgg is not None:
                pIsAgg[0] = 1  

        if pExpr.pList and nErr == 0:
            for i in range(n):
                nErr = exprCheck(pParse, pExpr.pList.a[i].pExpr, allowAgg and not isAgg, pIsAgg)
                if nErr != 0:
                    break 
    
    else:
        if pExpr.pLeft:
            nErr = exprCheck(pParse, pExpr.pLeft, allowAgg, pIsAgg)

        if nErr == 0 and pExpr.pRight:
            nErr = exprCheck(pParse, pExpr.pRight, allowAgg, pIsAgg)
            
        if nErr == 0 and pExpr.pList:
            for elem in pExpr.pList.a:
                nErr = exprCheck(pParse, elem.pExpr, allowAgg, pIsAgg)
                if nErr != 0:
                    break

    return nErr

def funcId(pToken: Token):
    funcMap = {
        "count": FN_Count,
        "min": FN_Min,
        "max": FN_Max,
        "sum": FN_Sum,
        "avg": FN_Avg,
        "fcnt": FN_Fcnt,
    }

    tokenStr = pToken.z.lower()
    return funcMap.get(tokenStr, FN_Unknown)

def exprAnalyzeAggregates(pParse: Parse, pExpr: Expr):
    nErr = 0

    if pExpr is None:
        return 0

    if pExpr.op == TK_COLUMN:
        aAgg = pParse.aAgg
        for i in range(pParse.nAgg):
            if aAgg[i].isAgg:
                continue
            if (aAgg[i].pExpr.iTable == pExpr.iTable and aAgg[i].pExpr.iColumn == pExpr.iColumn):
                break
        else:
            i = appendAggInfo(pParse)
            if i < 0:
                return 1
            pParse.aAgg[i].isAgg = 0
            pParse.aAgg[i].pExpr = pExpr
        pExpr.iAgg = i

    elif pExpr.op == TK_AGG_FUNCTION:
        if pExpr.iColumn == FN_Count or pExpr.iColumn == FN_Avg:
            if pParse.iAggCount >= 0:
                i = pParse.iAggCount
            else:
                i = appendAggInfo(pParse)
                if i < 0:
                    return 1
                pParse.aAgg[i].isAgg = 1
                pParse.aAgg[i].pExpr = None
                pParse.iAggCount = i
            if pExpr.iColumn == FN_Count:
                pExpr.iAgg = i
                return 0  # break에 해당

        aAgg = pParse.aAgg
        for i in range(pParse.nAgg):
            if not aAgg[i].isAgg:
                continue
            if exprCompare(aAgg[i].pExpr, pExpr):
                break
        else:
            i = appendAggInfo(pParse)
            if i < 0:
                return 1
            pParse.aAgg[i].isAgg = 1
            pParse.aAgg[i].pExpr = pExpr
        pExpr.iAgg = i

    else:
        if pExpr.pLeft:
            nErr = exprAnalyzeAggregates(pParse, pExpr.pLeft)
        if nErr == 0 and pExpr.pRight:
            nErr = exprAnalyzeAggregates(pParse, pExpr.pRight)
        if nErr == 0 and pExpr.pList:
            n = pExpr.pList.nExpr
            for i in range(n):
                nErr = exprAnalyzeAggregates(pParse, pExpr.pList.a[i].pExpr)
                if nErr != 0:
                    break

    return nErr

def appendAggInfo(pParse: Parse):
    try:
        pParse.aAgg = pParse.aAgg if pParse.aAgg else []
        pParse.aAgg.append(AggExpr())  # 새 항목 추가
        index = len(pParse.aAgg) - 1
        pParse.nAgg += 1
        return index
    except MemoryError:
        pParse.zErrMsg = "out of memory"
        pParse.nErr += 1
        return -1
    
def exprCompare(pA: Expr, pB: Expr):
    if pA is None:
        return pB is None
    elif pB is None:
        return False

    if pA.op != pB.op:
        return False

    if not exprCompare(pA.pLeft, pB.pLeft):
        return False

    if not exprCompare(pA.pRight, pB.pRight):
        return False

    if pA.pList:
        if pB.pList is None:
            return False
        if pA.pList.nExpr != pB.pList.nExpr:
            return False
        for i in range(pA.pList.nExpr):
            if not exprCompare(pA.pList.a[i].pExpr, pB.pList.a[i].pExpr):
                return False
    elif pB.pList:
        return False

    if pA.pSelect or pB.pSelect:
        return False

    if pA.token.z:
        if pB.token.z is None:
            return False
        if pB.token.n != pA.token.n:
            return False
        if pA.token.z.lower() != pB.token.z.lower():
            return False

    return True

def isConstant(p: Expr):
    if p.op in (TK_ID, TK_COLUMN, TK_DOT):
        return False
    else:
        if p.pLeft and not isConstant(p.pLeft):
            return False
        if p.pRight and not isConstant(p.pRight):
            return False
        if p.pList:
            for i in range(p.pList.nExpr):
                if not isConstant(p.pList.a[i].pExpr):
                    return False
    return True