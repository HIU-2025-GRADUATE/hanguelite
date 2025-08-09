from src.constant import SQLITE_OK
from src.expr import exprCode
from src.sqliteInt import Parse, ExprList, Select, IdList, Table, SRT_Table
from src.vdbe.vdbe import Vdbe
from src.vdbe.vdbeOp import OP_Open, OP_New, OP_Dup, OP_Null, OP_String, OP_Field, OP_MakeRecord, OP_Put, OP_Goto, \
    OP_Next, OP_Rewind, OP_Noop
from src.select import select as executeSelect


def insert(parse: Parse, tableName: str, exprList: ExprList, select: Select, targetColumns: IdList):
    table: Table = parse.db.findTable(tableName)

    validateTableWrite(table, parse, tableName)

    vdbe: Vdbe = parse.getVdbe()
    if not vdbe:
        return

    # count column number
    if select:
        srcTable = parse.nTab
        parse.nTab += 1
        vdbe.addOp(OP_Open, srcTable, 1, 0, 0)
        rc = executeSelect(parse, select, SRT_Table, srcTable)
        nGivenColumn = select.pEList.nExpr
    else:
        srcTable = -1
        nGivenColumn = exprList.nExpr

    # check the number of columns
    if not targetColumns and nGivenColumn != table.nCol:
        parse.nErr += 1
        raise Exception(f"table '{tableName}' has {table.nCol} columns, but {nGivenColumn} values are supplied")
    elif targetColumns and nGivenColumn != targetColumns.nId:
        parse.nErr += 1
        raise Exception(f"the number of given columns is {targetColumns.nId} but {nGivenColumn} values are supplied")

    # 입력으로 주어진 컬럼명 순서가 실제 저장할 테이블의 컬럼 순서와 다를 수 있으므로, 인덱스 맞춰주기
    if targetColumns:
        for i in range(targetColumns.nId):
            targetColumns.a[i].idx = -1

        for i in range(targetColumns.nId):
            for j in range(table.nCol):
                if targetColumns.a[i].zName == table.aCol[j].zName:
                    targetColumns.a[i].idx = j
                    break
            else:
                parse.nErr += 1
                raise Exception(f"column '{targetColumns.a[i].zName}' is not in table '{tableName}'")

    # insert
    base = parse.nTab
    vdbe.addOp(OP_Open, base, 1, table.zName, 0)
    # TODO : index 파일 세팅
    # for (idx=1, pIdx=pTab->pIndex; pIdx; pIdx=pIdx->pNext, idx++){
    #     sqliteVdbeAddOp(v, OP_Open, idx + base, 1, pIdx->zName, 0);
    # }

    if srcTable >= 0:
        vdbe.addOp(OP_Rewind, srcTable, 0, 0, 0)
        iBreak = vdbe.makeLabel()
        iCont = vdbe.addOp(OP_Next, srcTable, iBreak, 0, 0)
        pass

    # 레코드 구성
    vdbe.addOp(OP_New, 0, 0, 0, 0)
    if table.pIndex:
        vdbe.addOp(OP_Dup, 0, 0, 0, 0)
    for i in range(table.nCol):
        if not targetColumns:
            j = i
        else:
            for j in range(targetColumns.nId):
                if targetColumns.a[i].idx == i:
                    break

        # 기본값 세팅
        print(srcTable)
        if targetColumns and j == targetColumns.nId:
            zDflt = table.aCol[j].zDflt
            if not zDflt: # 기본값이 없는 경우
                vdbe.addOp(OP_Null, 0, 0, 0, 0)
            else:
                vdbe.addOp(OP_String, 0, 0, zDflt, 0)
        elif srcTable != -1:
            vdbe.addOp(OP_Field, srcTable, i, 0, 0)
        else:
            exprCode(parse, exprList.a[j].pExpr)

    # 레코드 제작
    vdbe.addOp(OP_MakeRecord, table.nCol, 0, 0, 0)
    vdbe.addOp(OP_Put, base, 0, 0, 0)

    # TODO : index 삽입 데이터 처리

    # TODO : table 삽입 시 반복 로직 추가
    if srcTable >= 0:
        vdbe.addOp(OP_Goto, 0, iCont, 0, 0)
        vdbe.addOp(OP_Noop, 0, 0, 0, iBreak)


def validateTableWrite(table: Table, parse: Parse, tableName: str):
    if not table:
        parse.nErr += 1
        raise Exception(f"Table '{tableName}' not found")

    if table.readOnly:
        parse.nErr += 1
        raise Exception(f"Table '{tableName}' is read-only")
