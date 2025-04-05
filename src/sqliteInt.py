from tokenToConstant import *

SRT_Callback = 1  
SRT_Mem      = 2  
SRT_Set      = 3  
SRT_Union    = 5  
SRT_Except   = 6  
SRT_Table    = 7  


class Column:
    """
    SQL 테이블의 한 컬럼에 대한 정보를 저장.
      - zName: 컬럼 이름
      - zDflt: 기본값 (Default value)
      - notNull: NOT NULL 제약 조건이 있으면 1, 없으면 0
    """
    def __init__(self):
        self.zName = ""      # 문자열
        self.zDflt = ""      # 문자열 (기본값)
        self.notNull = 0     # 정수 (불리언)

class Table:
    """
    SQL 테이블 하나를 메모리 내에서 표현.
      - zName: 테이블 이름
      - pHash: 같은 해시 값을 갖는 다음 Table (해시 체인용)
      - nCol: 컬럼의 개수
      - aCol: Column 객체들의 리스트 (각 컬럼에 대한 정보)
      - readOnly: 이 테이블이 읽기 전용이면 1, 아니면 0
      - pIndex: 이 테이블에 속한 인덱스들의 연결 리스트 (Index 객체)
    """
    def __init__(self):
        self.zName = ""      # 문자열
        self.pHash = None    # Table 객체 (해시 체인용)
        self.nCol = 0        # 정수
        self.aCol = []       # Column 객체들의 리스트
        self.readOnly = 0    # 정수 (불리언)
        self.pIndex = None   # Index 객체 (연결 리스트)

class Index:
    """
    SQL 인덱스 정보를 저장.
      - zName: 인덱스 이름
      - pHash: 같은 해시 값을 갖는 다음 인덱스 (해시 체인용)
      - nColumn: 인덱스에 포함된 컬럼의 개수
      - aiColumn: 인덱스에 사용된 컬럼의 번호들을 담은 정수 배열 (첫번째 컬럼은 0부터 시작)
      - pTable: 이 인덱스가 속한 테이블 (Table 객체)
      - isUnique: 유일 인덱스이면 1, 아니면 0
      - pNext: 같은 테이블에 속한 다음 인덱스
    """
    def __init__(self):
        self.zName = ""       # 문자열
        self.pHash = None     # Index 객체 (해시 체인용)
        self.nColumn = 0      # 정수
        self.aiColumn = []    # 정수 리스트 (컬럼 번호)
        self.pTable = None    # Table 객체
        self.isUnique = 0     # 정수 (불리언)
        self.pNext = None     # Index 객체 (연결 리스트)

class Token:
    """
    Lexer에서 생성한 토큰 정보를 저장.
      - z: 토큰의 텍스트
      - n: 토큰의 길이
    """
    def __init__(self):
        self.z = ""
        self.n = 0

class Expr:
    """
    SQL 표현식(파스 트리의 노드)를 나타냄.
      - op: 연산자 코드 (예: TK_ID, TK_COLUMN 등)
      - pLeft, pRight: 왼쪽, 오른쪽 서브트리 (Expr 객체)
      - pList: 함수 인자나 BETWEEN 등에서 사용되는 표현식 리스트 (ExprList 객체)
      - token: 기본 피연산자 토큰 (Token 객체)
      - span: 표현식 전체의 텍스트 (Token 객체)
      - iTable: TK_COLUMN인 경우, 참조하는 테이블의 번호 (pTabList에서의 인덱스 + pParse.nTab)
      - iColumn: TK_COLUMN인 경우, 참조하는 컬럼의 번호
      - iAgg: 집계함수 관련, aggregator에서 값을 추출할 인덱스
      - pSelect: 서브쿼리(SELECT 문)이면 그 SELECT 구조 (Select 객체)
    """
    def __init__(self):
        self.op = 0
        self.pLeft = None      # Expr 객체
        self.pRight = None     # Expr 객체
        self.pList = None      # ExprList 객체
        self.token = Token()   # Token 객체
        self.span = Token()    # Token 객체
        self.iTable = 0
        self.iColumn = 0
        self.iAgg = 0
        self.pSelect = None    # Select 객체

class ExprListItem:
    """
    ExprList의 각 항목을 저장하는 구조체.
      - pExpr: 표현식 (Expr 객체)
      - zName: 해당 표현식에 지정된 별칭(AS절) 또는 이름
      - sortOrder: 정렬 순서 (0: ASC, 1: DESC)
      - isAgg: 이 항목이 집계 함수인지 (1이면 집계 함수)
      - done: 처리 완료 플래그 (0 또는 1)
    """
    def __init__(self):
        self.pExpr = None      # Expr 객체
        self.zName = ""
        self.sortOrder = 0
        self.isAgg = 0
        self.done = 0

class ExprList:
    """
    여러 표현식을 목록으로 저장.
      - nExpr: 표현식의 개수
      - a: ExprListItem 객체들의 리스트
    """
    def __init__(self):
        self.nExpr = 0
        self.a = []  # ExprListItem 객체들의 리스트

class IdListItem:
    """
    식별자 목록(IdList)에서 하나의 항목을 나타냄.
      - zName: 식별자 이름 (예: 테이블명 또는 컬럼명)
      - zAlias: "AS" 구문에서 사용되는 별칭 (없으면 빈 문자열)
      - pTab: 해당 식별자가 참조하는 테이블 (Table 객체)
      - idx: 해당 테이블의 컬럼 인덱스 (정수)
    """
    def __init__(self):
        self.zName = ""
        self.zAlias = ""
        self.pTab = None      # Table 객체
        self.idx = -1

class IdList:
    """
    식별자 목록을 저장.
      - nId: 식별자의 개수
      - a: IdListItem 객체들의 리스트
    """
    def __init__(self):
        self.nId = 0
        self.a = []  # IdListItem 객체들의 리스트

class WhereInfo:
    """
    WHERE 절 처리 루프와 관련된 정보를 저장.
      - pParse: 파서 컨텍스트 (Parse 객체)
      - pTabList: 조인에 포함된 테이블 목록 (IdList 객체)
      - iContinue: 다음 레코드를 처리할 때 점프할 주소
      - iBreak: 루프를 빠져나갈 때 점프할 주소
      - base: OP_Open 명령어로 열린 첫 번째 커서의 인덱스 (pParse.nTab)
      - aIdx: 각 테이블에 대해 사용할 인덱스들의 배열 (최대 32개)
    """
    def __init__(self):
        self.pParse = None    # Parse 객체
        self.pTabList = None  # IdList 객체
        self.iContinue = 0
        self.iBreak = 0
        self.base = 0
        self.aIdx = [None] * 32  # 32개의 Index 객체를 위한 배열

class Select:
    """
    SELECT 문 전체를 표현하는 구조체.
      - isDistinct: DISTINCT가 사용되었으면 1, 아니면 0
      - pEList: 결과 컬럼(표현식) 목록 (ExprList 객체)
      - pSrc: FROM 절에서 사용하는 테이블 목록 (IdList 객체)
      - pWhere: WHERE 절 (Expr 객체)
      - pGroupBy: GROUP BY 절 (ExprList 객체)
      - pHaving: HAVING 절 (Expr 객체)
      - pOrderBy: ORDER BY 절 (ExprList 객체)
      - op: 조합 연산자 (TK_UNION, TK_ALL, TK_INTERSECT, TK_EXCEPT 중 하나)
      - pPrior: 복합 SELECT 문에서 이전 SELECT (Select 객체)
    """
    def __init__(self):
        self.isDistinct = 0
        self.pEList = None    # ExprList 객체
        self.pSrc = None      # IdList 객체
        self.pWhere = None    # Expr 객체
        self.pGroupBy = None  # ExprList 객체
        self.pHaving = None   # Expr 객체
        self.pOrderBy = None  # ExprList 객체
        self.op = 0
        self.pPrior = None    # Select 객체

class AggExpr:
    """
    집계 함수와 관련된 정보를 저장하는 구조체.
      - isAgg: 이 항목이 집계 함수이면 1, 아니면 0
      - pExpr: 해당 집계 표현식 (Expr 객체)
      
    주의: AggExpr.pExpr가 None이면 "count(*)" 같은 경우를 나타낸다.
    """
    def __init__(self):
        self.isAgg = 0
        self.pExpr = None     # Expr 객체

class Parse:
    """
    SQL 파서를 위한 컨텍스트 정보를 저장.
      - db: 메인 데이터베이스 객체 (sqlite 객체)
      - xCallback: 결과를 처리할 콜백 함수
      - pArg: 콜백 함수의 첫번째 인자
      - zErrMsg: 에러 메시지 (문자열)
      - sErrToken: 에러가 발생한 토큰 (Token 객체)
      - sFirstToken: 첫 번째로 파싱된 토큰 (Token 객체)
      - sLastToken: 마지막으로 파싱된 토큰 (Token 객체)
      - pNewTable: CREATE TABLE 중에 생성중인 테이블 (Table 객체)
      - pVdbe: 바이트코드를 실행하는 VDBE 엔진 (Vdbe 객체)
      - colNamesSet: 콜백에 사용할 컬럼 이름이 설정되었으면 1, 아니면 0
      - explain: EXPLAIN 플래그가 있으면 1, 아니면 0
      - initFlag: CREATE TABLE 재파싱시 사용되는 플래그
      - nErr: 지금까지 발생한 에러의 개수
      - nTab: 할당된 커서의 개수 (정수)
      - nMem: 사용 중인 메모리 셀의 개수
      - nSet: 사용 중인 집합(Set)의 개수
      - nAgg: 집계 표현식의 개수
      - aAgg: AggExpr 객체들의 리스트
      - iAggCount: count(*) 집계 함수의 인덱스 (없으면 -1)
      - useAgg: 집계 결과를 생성할 때 aggregator에서 값을 추출할지 여부 (1이면 사용)
    """
    def __init__(self):
        self.db = None             # sqlite 객체
        self.xCallback = None      # 콜백 함수
        self.pArg = None           # 콜백 함수의 첫번째 인자
        self.zErrMsg = ""
        self.sErrToken = Token()
        self.sFirstToken = Token()
        self.sLastToken = Token()
        self.pNewTable = None      # Table 객체
        self.pVdbe = None          # Vdbe 객체
        self.colNamesSet = 0
        self.explain = 0
        self.initFlag = 0
        self.nErr = 0
        self.nTab = 0
        self.nMem = 0
        self.nSet = 0
        self.nAgg = 0
        self.aAgg = []             # AggExpr 객체들의 리스트
        self.iAggCount = -1
        self.useAgg = 0


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
