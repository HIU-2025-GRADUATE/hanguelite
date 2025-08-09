from src.expr import exprResolveInSelect, exprResolveIds, exprCheck
from src.sqliteInt import Parse, Token, Expr, IdList, sqlite, Table
from src.vdbe.vdbe import Vdbe
from src.vdbe.vdbeOp import OP_ListOpen, OP_ListWrite, OP_ListRewind, OP_Open, OP_ListRead, OP_Delete, OP_Goto, OP_ListClose
from src.where import whereBegin, whereEnd


def deleteFrom(parse: Parse, tableName: Token, where: Expr):
    db: sqlite = parse.db

    tableList: IdList = IdList()
    tableList.idListAppend(tableName)

    for i in range(tableList.nId):
        tableList.a[i].pTab = db.findTable(tableList.a[i].zName)
        if tableList.a[i].pTab is None:
            parse.nErr += 1
            raise Exception(f"No such table : {tableName}")

        if tableList.a[i].pTab.readOnly:
            parse.nErr += 1
            raise Exception(f"table '{tableName}' is read-only")

    table: Table = tableList.a[0].pTab

    """ resolve the column names in all expressions """
    if where is not None:
        exprResolveInSelect(parse, where)
        if exprResolveIds(parse, tableList, where):
            return
        if exprCheck(parse, where, 0, []):
            return

    """ ************************* """
    """ | Begin generating code | """
    """ ************************* """
    v: Vdbe = parse.getVdbe()

    """ 1. Begin DB Scan """
    v.addOp(OP_ListOpen, 0, 0, 0, 0)
    whereInfo = whereBegin(parse, tableList, where, 1)

    """ 2. Remember the key of every item to be deleted """
    v.addOp(OP_ListWrite, 0, 0, 0, 0)

    """ 3. End DB scan loop """
    whereEnd(whereInfo)

    """ 4. 위에서 체크한 삭제할 레코드 key 기반으로 데이터 삭제 진행 """
    base = parse.nTab
    v.addOp(OP_ListRewind, 0, 0, 0, 0)
    v.addOp(OP_Open, base, 1, table.zName, 0)
    # TODO : Index Open
    end = v.makeLabel()
    addr = v.addOp(OP_ListRead, 0, end, 0, 0)
    # TODO : Index Delete
    v.addOp(OP_Delete, base, 0, 0, 0)
    v.addOp(OP_Goto, 0, addr, 0, 0)
    v.addOp(OP_ListClose, 0, 0, 0, end)
