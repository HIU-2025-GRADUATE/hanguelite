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
    'LIKE' : 'TK_LIKE'
}

# 토큰 이름 목록: parse.y에서 사용되는 토큰들과 SQLite의 tokenize.c에 있는 키워드들
tokens = (
    'TK_STAR', 'TK_ID', 'TK_DOT', 'TK_COLUMN', 'TK_IGNORE',
    'TK_STRING', 'TK_LP', 'TK_RP', 'TK_COMMA', 'TK_INTEGER', 
    'TK_FLOAT', 'TK_LT', 'TK_GT', 'TK_LE', 'TK_GE', 'TK_NE', 
    'TK_EQ'
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

# 식별자 처리: 예약어와 일반 ID 구분
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

# def t_STRING(t):
#     r'[a-zA-Z]+'
#     t.type = reserved.get(t.value.upper(), 'TK_STRING')
#     return t

# 에러 처리
def t_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()