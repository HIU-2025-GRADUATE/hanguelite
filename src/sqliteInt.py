from src.util import hashNoCase
from src.constant import SQLITE_OK, SQLITE_Initialized, SQLITE_BUSY
from src.tokenToConstant import *
from src.vdbe.vdbe import *

SRT_Callback = 1  
SRT_Mem      = 2  
SRT_Set      = 3  
SRT_Union    = 5  
SRT_Except   = 6  
SRT_Table    = 7  
FN_Unknown   = 0
FN_Count     = 1
FN_Min       = 2
FN_Max       = 3
FN_Sum       = 4
FN_Avg       = 5
FN_Fcnt      = 6

"""
    The number of entries in the in-memory hash array holding the database schema.
"""
N_HASH = 51

class Column:
    zName: str
    zDflt: str
    notNull: int

    def __init__(self, columnName: str):
        self.zName = columnName
        self.zDflt = ""
        self.notNull = 0

class Table:
    zName: str
    pHash: 'Table'
    nCol: int
    aCol: list[Column]
    readOnly: int
    pIndex: 'Index'

    def __init__(self, tableName: str):
        self.aCol = []
        self.zName = tableName
        self.pHash = None
        self.nCol = 0
        self.readOnly = 0
        self.pIndex = None

class Index:
    zName: str
    pHash: 'Index'
    nColumn: int
    aiColumn: list[int]
    pTable: Table
    isUnique: int
    pNext: 'Index'

    def __init__(self):
        self.aiColumn = []
        self.zName = ""
        self.pHash = None
        self.nColumn = 0
        self.pTable = None
        self.isUnique = 0
        self.pNext = None

class sqlite:
    pBe: Dbbe
    flags: int
    file_format: int
    nTable: int
    pBusyArg: object
    xBusyCallback: callable
    apTblHash: list['Table']
    apIdxHash: list['Index']

    def __init__(self):
      self.pBe = None
      self.flags = 0
      self.file_format = 0
      self.nTable = 0
      self.pBusyArg = None 
      self.xBusyCallback = None 
      self.apTblHash = [None] * N_HASH
      self.apIdxHash = [None] * N_HASH

    @staticmethod
    def open(filename: str):
        """main.c : sqlite_open()"""
        db = sqlite()
        db.pBe = Dbbe.open(filename, writeFlag=True, createFlag=True)
        if not db.pBe:
            return None

        db.file_format = 1
        rc = db.initialize()
        if rc != SQLITE_OK and rc != SQLITE_BUSY:
            db.close()
            return None

        return db


    def findTable(self, tableName: str) -> Table:
        h = hashNoCase(tableName, 0) % N_HASH
        pTable: Table = self.apTblHash[h]

        while pTable:
            if pTable.zName == tableName:
                return pTable

            pTable = pTable.pHash

        return None

    def findIndex(self, indexName: str) -> Index:
        h = hashNoCase(indexName, 0) % N_HASH
        pIndex: Index = self.apIdxHash[h]
        while pIndex:
            if pIndex.zName == indexName:
                return pIndex

            pIndex = pIndex.pHash

        return None

    def openCb(self, argc: int, argv: [str], azColName: [str]):
        """ main.c : sqliteOpenCb() """
        if argc == 2: # there is meta information (argv[1]) in the sqlite_master file. Typical meta information is the file format version
            # TODO : argc == 2 인 케이스 구현
            """
            if( sscanf(argv[1],"file format %d",&db->file_format)==1 ){
              return 0;
            }
            /* Unknown meta information.  Ignore it. */
            return 0;
            """
            pass

        if argc != 1:
            return 0

        parse = Parse(self)
        parse.initFlag = True # 테이블을 디스크에 생성하지 않음

        # execute master table create sql
        from main import runParser
        return runParser(parse, argv[0])



    def initialize(self):
        """ main.c : sqliteInit() """
        master_schema = ("CREATE TABLE " + MASTER_NAME + " (\n"
                         "  type text,\n"                       # table / index / meta 중 하나
                         "  name text,\n"                       # table 또는 index 이름
                         "  tbl_name text,\n"                   # 관련된 테이블 이름
                         "  sql text\n"                         # 이 레코드와 관련된 테이블의 CREATE 구문
                         ")")

        initProg = [
            VdbeOp(OP_Open,       0, 0, MASTER_NAME),
            VdbeOp(OP_Next,       0, 9),   # / * 1 * /
            VdbeOp(OP_Field,      0, 0),
            VdbeOp(OP_String,     0, 0, "meta"),
            VdbeOp(OP_Ne,         0, 1),
            VdbeOp(OP_Field,      0, 0),
            VdbeOp(OP_Field,      0, 3),
            VdbeOp(OP_Callback,   2, 0),
            VdbeOp(OP_Goto,       0, 1),
            VdbeOp(OP_Rewind,     0, 0),   # / *9 * /
            VdbeOp(OP_Next,       0, 17),  # / *10 * /
            VdbeOp(OP_Field,      0, 0),
            VdbeOp(OP_String,     0, 0, "table"),
            VdbeOp(OP_Ne,         0, 10),
            VdbeOp(OP_Field,      0, 3),
            VdbeOp(OP_Callback,   1, 0),
            VdbeOp(OP_Goto,       0, 10),
            VdbeOp(OP_Rewind,     0, 0),   # / *17 * /
            VdbeOp(OP_Next,       0, 25),  # / *18 * /
            VdbeOp(OP_Field,      0, 0),
            VdbeOp(OP_String,     0, 0, "index"),
            VdbeOp(OP_Ne,         0, 18),
            VdbeOp(OP_Field,      0, 3),
            VdbeOp(OP_Callback,   1, 0),
            VdbeOp(OP_Goto,       0, 18),
            VdbeOp(OP_Halt,       0, 0)    # / *25 * /
        ]

        vdbe = Vdbe(self.pBe)
        vdbe.addOpList(len(initProg), initProg)
        # OP_Open 에서 파일 없다는 에러 남.
        # 마스터 테이블 파일은 최초에 그냥 존재한다는 가정이 깔려있는 듯 함. (마스터 테이블 CREATE 구문도 실행은 하는데 디스크에 파일 저장은 안함)
        rc = vdbe.exec(xCallback=self.openCb) # 여기에서 실행시 에러

        # TODO : TEST
        rc = SQLITE_OK # TEST
        self.file_format = 2
        # TODO : TEST

        if rc == SQLITE_OK and self.file_format < 2 and self.nTable > 0:
            raise Exception("obsolete file format")
            # rc = SQLITE_ERROR

        if rc == SQLITE_OK:
            self.openCb(1, [master_schema, 0], [])
            table = self.findTable(MASTER_NAME)

            if table:
                table.readOnly = 1

            self.flags |= SQLITE_Initialized

        return rc


class Token:
    z: str
    n: int

    def __init__(self, token: str):
        self.z = token
        self.n = len(token)

    def __str__(self):
        return self.z


class Expr:
    op: int
    pLeft: 'Expr'
    pRight: 'Expr'
    pList: 'ExprList'
    token: Token
    span: Token
    iTable: int
    iColumn: int
    iAgg: int
    pSelect: 'Select'

    def __init__(self, op : int, pLeft : 'Expr', pRight : 'Expr', token : Token, opStr : str = None, pList : 'ExprList' = None):
        self.op = op
        self.pLeft = pLeft
        self.pRight = pRight
        self.token = token or Token("")
        self.pList = pList
        self.iTable = 0
        self.iColumn = 0
        self.iAgg = 0
        self.pSelect = None

        if pLeft and pRight:
            self.span = Token(pLeft.span.z + " " +  opStr + " " + pRight.span.z)
        else:
            self.span = self.token


class ExprListItem:
    pExpr: Expr
    zName: str
    sortOrder: int
    isAgg: int
    done: int

    def __init__(self):
        self.pExpr = None
        self.zName = ""
        self.sortOrder = 0
        self.isAgg = 0
        self.done = 0


class ExprList:
    nExpr: int
    a: list[ExprListItem]

    def __init__(self):
        self.a = []
        self.nExpr = 0
    
    def exprListAppend(self, pExpr : Expr, pName : Token):
        item = ExprListItem()
        item.pExpr = pExpr
        item.zName = ""

        if pName:
            item.zName = pName.z[:pName.n].strip()

        self.a.append(item)
        self.nExpr += 1


class IdListItem:
    zName: str
    zAlias: str
    pTab: Table
    idx: int

    def __init__(self):
        self.zName = ""
        self.zAlias = ""
        self.pTab = None
        self.idx = 0


class IdList:
    nId: int
    a: list[IdListItem]

    def __init__(self):
        self.a = []
        self.nId = 0

    def idListAppend(self, pToken : Token):
        self.a.append(IdListItem())
        if pToken:
            self.a[self.nId].zName = pToken.z[:pToken.n].strip()

        self.nId += 1

    def addAlias(self, pToken: Token):
        if self.nId > 0:
            if pToken.z[0] in ("'", '"'):
                pToken.z = pToken.z[1:-1].replace(pToken.z[0] * 2, pToken.z[0])
            
            self.a[-1].zAlias = pToken.z


class WhereInfo:
    pParse: 'Parse'
    pTabList: IdList
    iContinue: int
    iBreak: int
    base: int
    aIdx: list[Index]

    def __init__(self):
        self.pParse = None
        self.pTabList = None
        self.iContinue = 0
        self.iBreak = 0
        self.base = 0
        self.aIdx = [None] * 32


class Select:
    isDistinct: int
    pEList: ExprList
    pSrc: IdList
    pWhere: Expr
    pGroupBy: ExprList
    pHaving: Expr
    pOrderBy: ExprList
    op: int
    pPrior: 'Select'

    def __init__(self, pEList, pSrc, pWhere, pGroupBy, pHaving, pOrderBy, isDistinct):
        self.isDistinct = isDistinct
        self.pEList = pEList
        self.pSrc = pSrc
        self.pWhere = pWhere
        self.pGroupBy = pGroupBy
        self.pHaving = pHaving
        self.pOrderBy = pOrderBy
        self.op = TK_SELECT 
        self.pPrior = None


class AggExpr:
    isAgg: int
    pExpr: Expr

    def __init__(self):
        self.isAgg = 0
        self.pExpr = None
    
    
class Parse:
    db: sqlite
    xCallback: callable
    pArg: object
    zErrMsg: str
    sErrToken: Token
    sFirstToken: Token
    sLastToken: Token
    pNewTable: Table
    pVdbe: Vdbe
    colNamesSet: int
    explain: bool
    initFlag: bool
    nErr: int
    nTab: int
    nMem: int
    nSet: int
    nAgg: int
    aAgg: list[AggExpr]
    iAggCount: int
    useAgg: int

    def __init__(self, db: sqlite):
        self.db = db
        self.xCallback = None
        self.pArg = None
        self.zErrMsg = ""
        self.sErrToken = None
        self.sFirstToken = None
        self.sLastToken = None
        self.pNewTable = None
        self.pVdbe = None
        self.colNamesSet = 0
        self.explain = False
        self.initFlag = False
        self.nErr = 0
        self.nTab = 0
        self.nMem = 0
        self.nSet = 0
        self.nAgg = 0
        self.aAgg = []
        self.iAggCount = 0
        self.useAgg = 0

    def infoReset(self):
        self.aAgg = None
        self.nAgg = 0
        self.iAggCount = -1
        self.useAgg = 0

    def getVdbe(self):
        """ single tone"""
        v: Vdbe = self.pVdbe
        if not v:
            v = Vdbe(self.db.pBe)
            self.pVdbe = v

        return v

    @staticmethod
    def empty():
        return Parse()
