from src.util import hashNoCase
from src.tokenToConstant import *
from src.vdbe.vdbe import *

SRT_Callback = 1  
SRT_Mem      = 2  
SRT_Set      = 3  
SRT_Union    = 5  
SRT_Except   = 6  
SRT_Table    = 7  

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
        db.pBe = Dbbe.open(filename)
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


class Token:
    z: str
    n: int

    def __init__(self, token: str):
        self.z = token
        self.n = len(token)


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

    def __init__(self, op : int, pLeft : 'Expr', pRight : 'Expr', token : Token):
        self.op = op
        self.pLeft = pLeft
        self.pRight = pRight
        self.token = token or Token()
        self.pList = None
        self.iTable = 0
        self.iColumn = 0
        self.iAgg = 0
        self.pSelect = None

        if pLeft and pRight:
            self.span.z = pLeft.span.z
            #TODO 포인터 계산 처리 방법 고안
            # self.span.n = len(pRight.span.z) + (get_char_offset(pRight.span.z) - get_char_offset(pLeft.span.z))
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
        self.aAgg = 0
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
