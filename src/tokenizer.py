from ply import lex

# 예약어 사전 (대소문자 무시 처리)
reserved = {
    'SELECT': 'TK_SELECT',
    'FROM': 'TK_FROM',
    'IN' : 'TK_IN',
    'CREATE' : 'TK_CREATE',
    'TABLE' : 'TK_TABLE',
    'WHERE' : 'TK_WHERE',
    'AND' : 'TK_AND',
    'OR' : 'TK_OR',
    'LIKE' : 'TK_LIKE',
    'NOT' : 'TK_NOT',
    'INSERT' : 'TK_INSERT',
    'INTO' : 'TK_INTO',
    'VALUES' : 'TK_VALUES',
    'NULL': 'TK_NULL',
    'GROUP' : 'TK_GROUP',
    'BY': 'TK_BY',
    'HAVING' : 'TK_HAVING',
    'ISNULL' : 'TK_ISNULL',
    'NOTNULL' : 'TK_NOTNULL',
    'BETWEEN' : 'TK_BETWEEN',
    'DROP': 'TK_DROP',
    'ORDER' : 'TK_ORDER',
    'ASC' : 'TK_ASC',
    'DESC' : 'TK_DESC',
    'AS' : 'TK_AS',
    'UPDATE': 'TK_UPDATE',
    'SET': 'TK_SET',
    'DELETE': 'TK_DELETE',
}

# 토큰 이름 목록: parse.y에서 사용되는 토큰들과 SQLite의 tokenize.c에 있는 키워드들
tokens = (
    'TK_STAR', 'TK_ID', 'TK_DOT', 'TK_COLUMN', 'TK_IGNORE',
    'TK_STRING', 'TK_LP', 'TK_RP', 'TK_COMMA', 'TK_INTEGER', 
    'TK_FLOAT', 'TK_LT', 'TK_GT', 'TK_LE', 'TK_GE', 'TK_NE', 
    'TK_EQ', 'TK_PLUS', 'TK_MINUS',
    "TK_SELECT_KR", "TK_FROM_KR", "TK_WHERE_PRE_KR", "TK_WHERE_POST_KR", "TK_GROUP_BY_PRE_KR", "TK_GROUP_BY_POST_KR",
    "TK_HAVING_PRE_KR", "TK_HAVING_POST_KR", "TK_ORDER_BY_KR", "TK_ASC_KR", "TK_DESC_KR", "TK_COL_LIST_POST_KR", "TK_TABLE_KOR", "TK_CREATE_KOR",
    "TK_TABLE_INTO_KOR", "TK_INSERT_KOR", "TK_EURO", "TK_UPDATE_KOR", "TK_DELETE_KOR", "TK_DROP_KOR"
) + tuple(reserved.values())

# 정규표현식 규칙
t_TK_STAR                   = r'\*'
t_TK_DOT                    = r'\.'
t_TK_IGNORE                 = r' \t\n'
t_TK_LP                     = r'\('
t_TK_RP                     = r'\)'
t_TK_COMMA                  = r','
t_TK_LE                     = r'<='
t_TK_GE                     = r'>='
t_TK_NE                     = r'<>'
t_TK_EQ                     = r'='
t_TK_LT                     = r'<'
t_TK_GT                     = r'>'
t_TK_PLUS                   = r'\+'
t_TK_MINUS                  = r'-'
t_TK_FROM_KR                = r"테이블에서"
t_TK_WHERE_PRE_KR           = r"조건이"
t_TK_WHERE_POST_KR          = r"일\s*때"
t_TK_GROUP_BY_PRE_KR        = r"그룹을"
t_TK_GROUP_BY_POST_KR       = r"(으로|로)\s*묶고"
t_TK_HAVING_PRE_KR          = r"그중에서"
t_TK_HAVING_POST_KR         = r"인"
t_TK_COL_LIST_POST_KR       = r"(을|를)"
t_TK_ASC_KR                 = r"오름차순"
t_TK_DESC_KR                = r"내림차순"
t_TK_ORDER_BY_KR            = r"(으로|로)\s*정렬해서"
t_TK_SELECT_KR              = r"찾아줘"
t_TK_TABLE_KOR              = r"테이블을"
t_TK_CREATE_KOR             = r"만들어줘"
t_TK_TABLE_INTO_KOR         = r"테이블에"
t_TK_INSERT_KOR             = r"추가해줘"
t_TK_EURO                   = r"(으로|로)"
t_TK_UPDATE_KOR             = r"(변경해줘|바꿔줘)"
t_TK_DELETE_KOR             = r"(삭제해줘|지워줘)"
t_TK_DROP_KOR               = r"제거해줘"

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'TK_ID')
    return t

def t_FLOAT(t):
    r'[0-9]+\.[0-9]+'
    t.type = 'TK_FLOAT'
    return t

def t_INTEGER(t):
    r'[0-9]+'
    t.type = 'TK_INTEGER'
    return t

def t_STRING(t):
    r'(\'([^\']|\'\')*\')|(\"([^\"]|\"\")*\")'
    value = t.value[1:-1]
    value = value.replace(t.value[0]*2, t.value[0])
    t.value = value
    t.type = 'TK_STRING'
    return t

def t_AS(t):
    r'(으로서|로서)'
    t.type = 'TK_AS'
    return t

# 에러 처리
def t_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()