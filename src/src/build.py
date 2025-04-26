from src.src.sqliteInt import *
from src.src.vdbe.vdbeOp import *
from util import *

# 원형 : sqliteExec
def execute(pParse : Parse):
    if pParse.pVdbe:
        if pParse.explain:
            # sqliteVdbeList(pParse.pVdbe, pParse.xCallback, pParse.pArg, pParse.zErrMsg)
            pass
        else:
            # trace = sys.stderr if (pParse.db.flags & SQLITE_VdbeTrace) != 0 else None
            # sqliteVdbeTrace(pParse.pVdbe, trace)
            pParse.pVdbe.exec(
                pParse.xCallback,
                pParse.pArg,
                pParse.zErrMsg,
                pParse.db.pBusyArg,
                pParse.db.xBusyCallback
            )
        pParse.pVdbe.delete()
        pParse.pVdbe = None
        pParse.colNamesSet = False

def findTable(db : sqlite, zName : str):
    h = hashNoCase(zName, 0) % N_HASH
    pTable = db.apTblHash[h]

    while pTable:
        if pTable.zName == zName:
            return pTable
        pTable = pTable.pHash

    return None


"""
    메모리에 새로운 테이블 정보를 저장
    CREATE TABLE 구문을 처리할 때 처음으로 실행되는 함수
"""
def startTable(parse: Parse, zName: str):
    """ TEST """ #
    print("called startTable")
    parse.pNewTable = Table(zName) # TEST CODE
    return # TEST CODE
    """ TEST""" #

    db: sqlite = parse.db
    table: Table = db.findTable(zName)

    if table:
        parse.zErrMsg = "table %s already exists" % zName
        parse.nErr += 1
        return

    if db.findIndex(zName):
        parse.zErrMsg = "there is already an index named %s" % zName
        parse.nErr += 1
        return

    parse.pNewTable = Table(zName)


"""
    이 함수는 CREATE TABLE 구문에서 마지막 ")" 문자를 만났을 때 호출한다.
    
    내부 해시 테이블에 '테이블 구조' 정보를 저장한다.
    
    initFlag == 1 이 아니라면, 이 테이블에 대한 entry를 디스크에 있는 마스터 테이블에 저장한다.
    initFlag == 1 이라면 이제 처음으로 데이터베이스에 연결했기 때문에 마스터 테이블을 읽고 있다는 것을 의미한다.
    따라서 이 경우엔 이 테이블에 대한 entry 가 마스터 테이블에 이미 존재하며, 다시 새로 만들지 않는다.  
"""
def endTable(parse: Parse, createQuery: str):
    """ TEST """  #
    print("called endTable")
    return  # TEST CODE
    """ TEST"""  #

    if parse.nErr != 0:
        return

    table: Table = parse.pNewTable

    # True to insert a meta records into the file
    addMeta = table != None and parse.db.nTable == 1

    # Add the table to the in-memory representation of the database
    if table and not parse.explain:
        h = hashNoCase(table.zName, 0) % N_HASH
        table.hash = parse.db.apTblHash[h]
        parse.db.apTblHash[h] = table
        parse.pNewTable = None
        parse.db.nTable += 1

    # If not initializing, then create the table on disk.
    if not parse.initFlag:
        addTableOps: [VdbeOp] = [
            VdbeOp( OP_Open,         0, 1, MASTER_NAME ),
            VdbeOp( OP_New,          0, 0 ),
            VdbeOp( OP_String,       0, 0, "table" ),
            VdbeOp( OP_String,       0, 0, table.zName ),
            VdbeOp( OP_String,       0, 0, table.zName ),
            VdbeOp( OP_String,       0, 0, createQuery ),
            VdbeOp( OP_MakeRecord,   4, 0 ),
            VdbeOp( OP_Put,          0, 0 ),
        ]

        vdbe: Vdbe = parse.getVdbe()
        if not vdbe:
            return

        vdbe.addOpList(len(addTableOps), addTableOps)

        addVersionOps: [VdbeOp] = [
            VdbeOp( OP_New,          0, 0 ),
            VdbeOp( OP_String,       0, 0, "meta" ),
            VdbeOp( OP_String,       0, 0, "" ),
            VdbeOp( OP_String,       0, 0, "" ),
            VdbeOp( OP_String,       0, 0, "file format 2" ),
            VdbeOp( OP_MakeRecord,   4, 0 ),
            VdbeOp( OP_Put,          0, 0 ),
        ]

        if addMeta:
            vdbe.addOpList(len(addVersionOps), addVersionOps)

        vdbe.addOp(OP_Close, 0, 0, None, 0)


"""
    Add a new column to the table currently being constructed.
"""
def addColumn(parse: Parse, columnName: str):
    table: Table = parse.pNewTable
    if not table:
        return

    column: Column = Column(columnName)
    table.aCol.append(column)
