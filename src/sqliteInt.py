from typing import List, Optional

SRT_Callback = 1  
SRT_Mem      = 2  
SRT_Set      = 3  
SRT_Union    = 5  
SRT_Except   = 6  
SRT_Table    = 7  


class Token:
    """Lexer에서 생성된 토큰을 표현하는 클래스"""
    def __init__(self):
        self.z: Optional[str] = None  # 토큰의 문자열
        self.n: int = 0  # 토큰 길이


class Column:
    """SQL 테이블의 개별 열 정보를 저장하는 클래스"""
    def __init__(self):
        self.zName: Optional[str] = None  # 열 이름
        self.zDflt: Optional[str] = None  # 기본값
        self.notNull: int = 0  # NOT NULL 제약 조건 여부


class Table:
    """SQL 테이블을 메모리에 저장하는 클래스"""
    def __init__(self):
        self.zName: Optional[str] = None  # 테이블 이름
        self.pHash: Optional['Table'] = None  # 동일한 해시 값을 가진 다음 테이블
        self.nCol: int = 0  # 테이블의 열 개수
        self.aCol: Optional[List[Column]] = None  # 열 목록
        self.readOnly: int = 0  # 읽기 전용 여부
        self.pIndex: Optional['Index'] = None  # 테이블의 인덱스 목록


class Index:
    """SQL 인덱스를 저장하는 클래스"""
    def __init__(self):
        self.zName: Optional[str] = None  # 인덱스 이름
        self.pHash: Optional['Index'] = None  # 동일한 해시 값을 가진 다음 인덱스
        self.nColumn: int = 0  # 인덱스된 열 개수
        self.aiColumn: Optional[List[int]] = None  # 인덱스된 열들의 테이블 내 위치
        self.pTable: Optional[Table] = None  # 인덱스가 속한 테이블
        self.isUnique: int = 0  # 인덱스가 유니크 여부
        self.pNext: Optional['Index'] = None  # 같은 테이블의 다음 인덱스


class Expr:
    """SQL 표현식을 나타내는 노드"""
    def __init__(self):
        self.op: int = 0  # 연산자 코드
        self.pLeft: Optional['Expr'] = None  # 왼쪽 자식 표현식
        self.pRight: Optional['Expr'] = None  # 오른쪽 자식 표현식
        self.pList: Optional['ExprList'] = None  # 표현식 리스트 (함수 호출 시 사용)
        self.token: Token = Token()  # 연산자 또는 피연산자 토큰
        self.span: Token = Token()  # 전체 표현식의 원본 문자열
        self.iTable: int = 0  # 테이블 인덱스
        self.iColumn: int = 0  # 컬럼 인덱스 또는 함수 ID
        self.iAgg: int = 0  # 집계 연산 인덱스
        self.pSelect: Optional['Select'] = None  # 서브쿼리


class ExprList:
    """여러 개의 표현식을 관리하는 리스트"""
    class ExprItem:
        """ExprList 내부의 개별 항목"""
        def __init__(self):
            self.pExpr: Optional[Expr] = None  # 표현식
            self.zName: Optional[str] = None  # 별칭
            self.sortOrder: int = 0  # 정렬 순서 (1 = DESC, 0 = ASC)
            self.isAgg: int = 0  # 집계 함수 여부
            self.done: int = 0  # 처리 완료 여부

    def __init__(self):
        self.nExpr: int = 0  # 표현식 개수
        self.a: Optional[List[ExprList.ExprItem]] = None  # 표현식 목록


class IdList:
    """SQL 식별자 목록을 저장하는 클래스"""
    class IdItem:
        """IdList 내부의 개별 항목"""
        def __init__(self):
            self.zName: Optional[str] = None  # 식별자 이름
            self.zAlias: Optional[str] = None  # 별칭
            self.pTab: Optional[Table] = None  # 테이블 참조
            self.idx: int = -1  # 테이블의 특정 컬럼 인덱스

    def __init__(self):
        self.nId: int = 0  # 식별자 개수
        self.a: Optional[List[IdList.IdItem]] = None  # 식별자 목록


class WhereInfo:
    """WHERE 절 처리에 필요한 정보 저장"""
    def __init__(self):
        self.pParse: Optional['Parse'] = None  # 파서 객체
        self.pTabList: Optional[IdList] = None  # 조인된 테이블 목록
        self.iContinue: int = 0  # 다음 레코드로 이동하는 점프 위치
        self.iBreak: int = 0  # 루프 탈출 점프 위치
        self.base: int = 0  # Open 연산자의 인덱스
        self.aIdx: List[Optional[Index]] = [None] * 32  # 테이블별 사용된 인덱스 리스트


class Select:
    """SQL SELECT 문을 표현하는 클래스"""
    def __init__(self):
        self.isDistinct: int = 0  # DISTINCT 여부
        self.pEList: Optional[ExprList] = None  # SELECT 결과 필드 리스트
        self.pSrc: Optional[IdList] = None  # FROM 절에 포함된 테이블 목록
        self.pWhere: Optional[Expr] = None  # WHERE 절 표현식
        self.pGroupBy: Optional[ExprList] = None  # GROUP BY 절 리스트
        self.pHaving: Optional[Expr] = None  # HAVING 절 표현식
        self.pOrderBy: Optional[ExprList] = None  # ORDER BY 절 리스트
        self.op: int = 0  # 집합 연산자 (UNION, INTERSECT 등)
        self.pPrior: Optional['Select'] = None  # 이전 SELECT 문 (컴파운드 쿼리)

class AggExpr:
    def __init__(self):
        self.isAgg = 0        # if TRUE contains an aggregate function
        self.pExpr = None     # The expression (Expr 객체)


class Parse:
    def __init__(self):
        self.db = None            # The main database structure
        self.xCallback = None      # The callback function
        self.pArg = None           # First argument to the callback function
        self.zErrMsg = None        # An error message
        self.sErrToken = Token()   # The token at which the error occurred
        self.sFirstToken = Token() # The first token parsed
        self.sLastToken = Token()  # The last token parsed
        self.pNewTable = None      # A table being constructed by CREATE TABLE
        self.pVdbe = None          # An engine for executing database bytecode
        self.colNamesSet = 0       # TRUE after OP_ColumnCount has been issued to pVdbe
        self.explain = 0           # True if the EXPLAIN flag is found on the query
        self.initFlag = 0          # True if reparsing CREATE TABLEs
        self.nErr = 0              # Number of errors seen
        self.nTab = 0              # Number of previously allocated cursors
        self.nMem = 0              # Number of memory cells used so far
        self.nSet = 0              # Number of sets used so far
        self.nAgg = 0              # Number of aggregate expressions
        self.aAgg = []             # List of AggExpr objects (replacing C-style array)
        self.iAggCount = -1        # Index of the count(*) aggregate in aAgg[]
        self.useAgg = 0            # If true, extract field values from the aggregator


# 사용 예시
# col1 = Column()
# col1.zName = "id"
# col1.zDflt = "0"
# col1.notNull = 1

# col2 = Column()
# col2.zName = "name"

# table = Table()
# table.zName = "Students"
# table.nCol = 2
# table.aCol = [col1, col2]

# index = Index()
# index.zName = "idx_students_id"
# index.nColumn = 1
# index.aiColumn = [0]
# index.pTable = table
# index.isUnique = 1

# expr = Expr()
# expr.op = 10
# expr.token.z = "id"
# expr.token.n = 2

# print(f"Table: {table.zName}, Columns: {[col.zName for col in table.aCol]}")
# print(f"Index: {index.zName}, Columns Indexed: {index.aiColumn}")
# print(f"Expr Token: {expr.token.z}")
