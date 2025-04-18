from sqliteInt import *


class ExprInfo:
        p : Expr
        indexable : int
        idxLeft : int
        idxRight : int
        prereqLeft : int
        prereqRight : int

        def __init__(self):
            self.p = None
            self.indexable = 0
            self.idxLeft = -1
            self.idxRight = -1
            self.prereqLeft = 0
            self.prereqRight = 0

def exprSplit(nSlot : int, aSlot : list[ExprInfo], pExpr : Expr):
    cnt = 0
    if pExpr is None or nSlot < 1:
        return 0
    if nSlot == 1 or pExpr.op != TK_AND:
        e = ExprInfo()
        e.p = pExpr
        aSlot.append(e)
        return 1
    if pExpr.pLeft.op != TK_AND:
        e = ExprInfo()
        e.p = pExpr.pLeft
        aSlot.append(e)
        cnt = 1 + exprSplit(nSlot - 1, aSlot, pExpr.pRight)
    else:
        cnt = exprSplit(nSlot, aSlot, pExpr.pRight)
        cnt += exprSplit(nSlot - cnt, aSlot, pExpr.pLeft)
    return cnt

def exprTableUsage(base : int, p : Expr):
    mask = 0
    if p is None:
        return 0
    if p.op == TK_COLUMN:
        return 1 << (p.iTable - base)
    if p.pRight:
        mask = exprTableUsage(base, p.pRight)
    if p.pLeft:
        mask |= exprTableUsage(base, p.pLeft)
    return mask

def exprAnalyze(base : int, pInfo : ExprInfo):
    pExpr = pInfo.p
    pInfo.prereqLeft = exprTableUsage(base, pExpr.pLeft)
    pInfo.prereqRight = exprTableUsage(base, pExpr.pRight)
    pInfo.indexable = 0
    pInfo.idxLeft = -1
    pInfo.idxRight = -1
    if pExpr.op == TK_EQ and (pInfo.prereqRight & pInfo.prereqLeft) == 0:
        if pExpr.pRight.op == TK_COLUMN:
            pInfo.idxRight = pExpr.pRight.iTable - base
            pInfo.indexable = 1
        if pExpr.pLeft.op == TK_COLUMN:
            pInfo.idxLeft = pExpr.pLeft.iTable - base
            pInfo.indexable = 1

def whereBegin(pParse : Parse, pTabList : IdList, pWhere : Expr, pushKey : int):
    v = pParse.pVdbe
    aOrder = [0] * pTabList.nId
    pWInfo = WhereInfo()

    pWInfo.pParse = pParse
    pWInfo.pTabList = pTabList
    base = pWInfo.base = pParse.nTab

    aExpr = []
    nExpr = exprSplit(50, aExpr, pWhere)   

    for i in range(nExpr):
        exprAnalyze(pParse.nTab, aExpr[i])         

    for i in range(pTabList.nId):
        aOrder[i] = i

    aIdx = [None] * 32
    loopMask = 0
    for i in range(min(pTabList.nId, len(aIdx))):
        idx = aOrder[i]
        pTab = pTabList.a[idx].pTab
        pIdx = pTab.pIndex
        pBestIdx = None

        # while pIdx:
        #     if pIdx.nColumn > 32:
        #         pIdx = pIdx.pNext
        #         continue

        #     columnMask = 0
        #     for j in range(nExpr):
        #         if aExpr[j].idxLeft == idx and (aExpr[j].prereqRight & loopMask) == aExpr[j].prereqRight:
        #             iColumn = aExpr[j].p.pLeft.iColumn
        #             for k in range(pIdx.nColumn):
        #                 if pIdx.aiColumn[k] == iColumn:
        #                     columnMask |= 1 << k
        #                     break
        #         if aExpr[j].idxRight == idx and (aExpr[j].prereqLeft & loopMask) == aExpr[j].prereqLeft:
        #             iColumn = aExpr[j].p.pRight.iColumn
        #             for k in range(pIdx.nColumn):
        #                 if pIdx.aiColumn[k] == iColumn:
        #                     columnMask |= 1 << k
        #                     break
        #     if columnMask + 1 == (1 << pIdx.nColumn):
        #         if pBestIdx is None or pBestIdx.nColumn < pIdx.nColumn:
        #             pBestIdx = pIdx
        #     pIdx = pIdx.pNext

        aIdx[i] = pBestIdx
        loopMask |= 1 << idx

    for i in range(pTabList.nId):
        v.addOp(OP_Open, base + i, 0, pTabList.a[i].pTab.zName, 0)
        if i < len(aIdx) and aIdx[i] is not None:
            v.addOp(OP_Open, base + pTabList.nId + i, 0, aIdx[i].zName, 0)

    pWInfo.aIdx = aIdx
    pWInfo.iBreak = brk = v.makeLabel()
    loopMask = 0

    for i in range(pTabList.nId):
        idx = aOrder[i]
        pIdx = aIdx[i] if i < len(aIdx) else None
        cont = v.makeLabel()

        if pIdx is None:
            v.addOp(OP_Next, base + idx, brk, 0, cont)
            haveKey = False
        # else:
        #     for j in range(pIdx.nColumn):
        #         for k in range(nExpr):
        #             if aExpr[k].p is None:
        #                 continue
        #             if (aExpr[k].idxLeft == idx and
        #                 (aExpr[k].prereqRight & loopMask) == aExpr[k].prereqRight and
        #                 aExpr[k].p.pLeft.iColumn == pIdx.aiColumn[j]):
        #                 sqliteExprCode(pParse, aExpr[k].p.pRight)
        #                 aExpr[k].p = None
        #                 break
        #             if (aExpr[k].idxRight == idx and
        #                 (aExpr[k].prereqLeft & loopMask) == aExpr[k].prereqLeft and
        #                 aExpr[k].p.pRight.iColumn == pIdx.aiColumn[j]):
        #                 sqliteExprCode(pParse, aExpr[k].p.pLeft)
        #                 aExpr[k].p = None
        #                 break
        #     sqliteVdbeAddOp(v, OP_MakeKey, pIdx.nColumn, 0, 0, 0)
        #     sqliteVdbeAddOp(v, OP_Fetch, base + pTabList.nId + i, 0, 0, 0)
        #     sqliteVdbeAddOp(v, OP_NextIdx, base + pTabList.nId + i, brk, 0, cont)
        #     if i == pTabList.nId - 1 and pushKey:
        #         haveKey = True
        #     else:
        #         sqliteVdbeAddOp(v, OP_Fetch, idx, 0, 0, 0)
        #         haveKey = False

        loopMask |= 1 << idx

        # for j in range(nExpr):
        #     if aExpr[j].p is None:
        #         continue
        #     if ((aExpr[j].prereqRight & loopMask) != aExpr[j].prereqRight or
        #         (aExpr[j].prereqLeft & loopMask) != aExpr[j].prereqLeft):
        #         continue
        #     if haveKey:
        #         sqliteVdbeAddOp(v, OP_Fetch, base + idx, 0, 0, 0)
        #         haveKey = False
        #     sqliteExprIfFalse(pParse, aExpr[j].p, cont)
        #     aExpr[j].p = None

        brk = cont

    pWInfo.iContinue = cont
    if pushKey and not haveKey:
        v.addOp(OP_Key, base, 0, 0, 0)

    return pWInfo

def whereEnd(pWInfo : WhereInfo):
    v = pWInfo.pParse.pVdbe
    brk = pWInfo.iBreak
    base = pWInfo.base

    v.addOp(OP_Goto, 0, pWInfo.iContinue, 0, 0)

    for i in range(pWInfo.pTabList.nId):
        v.addOp(OP_Close, base + i, 0, 0, brk)
        brk = 0
        if i < len(pWInfo.aIdx) and pWInfo.aIdx[i] is not None:
            v.addOp(OP_Close, base + pWInfo.pTabList.nId + i, 0, 0, 0)

    if brk != 0:
        v.addOp(OP_Noop, 0, 0, 0, brk)
