from src.expr import exprResolveInSelect, exprResolveIds, exprCheck, exprCode
from src.sqliteInt import Parse, ExprList, Expr, IdList, Token, Table, WhereInfo
from src.vdbe.vdbe import Vdbe
from src.vdbe.vdbeOp import OP_ListOpen, OP_ListWrite, OP_ListRewind, OP_Open, OP_Field, OP_MakeRecord, OP_Put, OP_Goto, \
    OP_ListClose, OP_ListRead, OP_Dup, OP_Fetch
from src.where import whereBegin, whereEnd


class UpdateCleanUp(Exception):
    pass

def update(pParse: Parse, tableName: Token, setList: ExprList, whereOpt: Expr):
    print("[UPDATE] update start")
    try:
        tableList: IdList = IdList()
        tableList.idListAppend(tableName)

        for i in range(tableList.nId):
            tableList.a[i].pTab = pParse.db.findTable(tableName.z)

            if tableList.a[i].pTab is None:
                pParse.nErr += 1
                raise UpdateCleanUp(f"Table {tableName.z} not found")

            if tableList.a[i].pTab.readOnly:
                pParse.nErr += 1
                raise UpdateCleanUp(f"Table {tableName.z} is read-only")

        table: Table = tableList.a[0].pTab
        updateColumnIdx = [-1] * table.nCol

        if whereOpt:
            exprResolveInSelect(pParse, whereOpt)

        for i in range(setList.nExpr):
            exprResolveInSelect(pParse, setList.a[i].pExpr)

        if whereOpt:
            if exprResolveIds(pParse, tableList, whereOpt):
                raise UpdateCleanUp()
            if exprCheck(pParse, whereOpt, 0, None):
                raise UpdateCleanUp()

        for i in range(setList.nExpr):
            if exprResolveIds(pParse, tableList, setList.a[i].pExpr):
                raise UpdateCleanUp()
            if exprCheck(pParse, setList.a[i].pExpr, 0, None):
                raise UpdateCleanUp()

            for j in range(table.nCol):
                if table.aCol[j].zName == setList.a[i].zName:
                    updateColumnIdx[j] = i
                    break
            else:
                pParse.nErr += 1
                raise UpdateCleanUp(f"no such column : {setList.a[i].zName}")

        # TODO : Index 처리
        #/* Allocate memory for the array apIdx[] and fill it pointers to every
        #** index that needs to be updated. Indices only need updating if their
        #** key includes one of the columns named in pChanges.
        #*/
        #for (nIdx=0, pIdx=pTab->pIndex; pIdx; pIdx=pIdx->pNext){
        #    for (i=0; i < pIdx->nColumn; i++){
        #        if ( aXRef[pIdx->aiColumn[i]] >= 0 )
        #            break;
        #        }
        #    if (i < pIdx->nColumn) nIdx++;
        #}
        #apIdx = sqliteMalloc( sizeof(Index * ) * nIdx );
        #if ( apIdx == 0 ) goto update_cleanup;
        #for (nIdx=0, pIdx=pTab->pIndex; pIdx; pIdx=pIdx->pNext){
        #for (i=0; i < pIdx->nColumn; i++){
        #if (aXRef[pIdx->aiColumn[i]] >= 0) break;
        #}
        #if (i < pIdx->nColumn) apIdx[nIdx++] = pIdx;
        #}

        # Begin Generate Code
        v: Vdbe = pParse.getVdbe()
        if not v:
            raise UpdateCleanUp()

        # Begin the Database Scan
        v.addOp(OP_ListOpen, 0, 0, 0, 0)
        whereInfo: WhereInfo = whereBegin(pParse, tableList, whereOpt, 1)
        if not whereInfo:
            raise UpdateCleanUp()

        # Remember the index of every item to be updated
        v.addOp(OP_ListWrite, 0, 0, 0, 0)

        # end the database scan loop
        whereEnd(whereInfo)

        # Rewind the list of records that need to be updated
        # and open every index that needs updating.
        v.addOp(OP_ListRewind, 0, 0, 0, 0)
        base = pParse.nTab
        v.addOp(OP_Open, base, 1, table.zName, 0)
        # for (i=0; i < nIdx; i++){
        #     sqliteVdbeAddOp(v, OP_Open, base + i + 1, 1, apIdx[i]->zName, 0);
        # }

        # Loop over every  records that needs updating.
        # We have to load the old data for each record to be updated
        # because some columns might not change and we will need to copy the old value
        # Also, the old data is needed to delete the old index entries.
        end = v.makeLabel()
        addr = v.addOp(OP_ListRead, 0, end, 0, 0)
        v.addOp(OP_Dup, 0, 0, 0, 0)
        v.addOp(OP_Fetch, base, 0, 0, 0)

        # TODO : index 삭제

        # compute a completely new data for this record
        for i in range(table.nCol):
            j = updateColumnIdx[i]
            if j < 0:
                v.addOp(OP_Field, base, i, 0, 0)
            else:
                exprCode(pParse, setList.a[j].pExpr)

        # TODO :new index 삽입

        # write the new data back into the database
        v.addOp(OP_MakeRecord, table.nCol, 0, 0, 0)
        v.addOp(OP_Put, base, 0, 0, 0)

        # repeat the above with the next record to be updated,
        # until all record selected by the WHERE clause have been updated.
        v.addOp(OP_Goto, 0, addr, 0, 0)
        v.addOp(OP_ListClose, 0, 0, 0, end)
    except Exception as e:
        raise e
    finally:
        # sqliteFree(apIdx);
        # sqliteFree(aXRef);
        # sqliteIdListDelete(pTabList);
        # sqliteExprListDelete(pChanges);
        # sqliteExprDelete(pWhere);
        return