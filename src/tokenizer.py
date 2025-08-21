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
    'DROP': 'TK_DROP',
}

# 토큰 이름 목록: parse.y에서 사용되는 토큰들과 SQLite의 tokenize.c에 있는 키워드들
tokens = (
    'TK_STAR', 'TK_ID', 'TK_DOT', 'TK_COLUMN', 'TK_IGNORE',
    'TK_STRING', 'TK_LP', 'TK_RP', 'TK_COMMA', 'TK_INTEGER', 
    'TK_FLOAT', 'TK_LT', 'TK_GT', 'TK_LE', 'TK_GE', 'TK_NE', 
    'TK_EQ', 'TK_PLUS', 'TK_MINUS'
) + tuple(reserved.values())

# 정규표현식 규칙
t_TK_STAR       = r'\*'
t_TK_DOT        = r'\.'
t_TK_IGNORE     = r' \t\n'
t_TK_LP         = r'\('
t_TK_RP         = r'\)'
t_TK_COMMA      = r','
t_TK_LE         = r'<='
t_TK_GE         = r'>='
t_TK_NE         = r'<>'
t_TK_EQ         = r'='
t_TK_LT         = r'<'
t_TK_GT         = r'>'
t_TK_PLUS       = r'\+'
t_TK_MINUS      = r'-'

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

# 에러 처리
def t_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()