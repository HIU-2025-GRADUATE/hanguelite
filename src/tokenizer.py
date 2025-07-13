from ply import lex

# 예약어 사전 (대소문자 무시 처리)
reserved = {
    'SELECT': 'TK_SELECT',
    'FROM': 'TK_FROM',
    'IN' : 'TK_IN',
    'CREATE' : 'TK_CREATE',
    'TABLE' : 'TK_TABLE',
    'INSERT' : 'TK_INSERT',
    'INTO' : 'TK_INTO',
    'VALUES' : 'TK_VALUES',
    'NULL': 'TK_NULL',
}

# 토큰 이름 목록: parse.y에서 사용되는 토큰들과 SQLite의 tokenize.c에 있는 키워드들
tokens = (
    'TK_STAR', 'TK_ID', 'TK_DOT', 'TK_COLUMN', 'TK_IGNORE',
    'TK_STRING', 'TK_LP', 'TK_RP', 'TK_COMMA', 'TK_PLUS', 'TK_MINUS', 'TK_INT'
) + tuple(reserved.values())

# 정규표현식 규칙
t_TK_STAR       = r'\*'
t_TK_DOT        = r'\.'
t_TK_IGNORE     = r' \t\n'
t_TK_LP         = r'\('
t_TK_RP         = r'\)'
t_TK_COMMA      = r','
t_TK_PLUS       = r'\+'
t_TK_MINUS      = r'-'

t_ignore        = ' \t'

# 식별자 처리: 예약어와 일반 ID 구분
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'TK_ID')
    return t

def t_STRING(t):
    # TODO : ' ' 형태도 문자열로 인식하도록 수정
    r'["][a-zA-Z]+["]'
    t.type = 'TK_STRING'
    return t

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    t.type = 'TK_INT'
    return t

# def t_FLOAT(t):
#     r'\d+'
#     t.value = float(t.value)
#     t.type = 'TK_FLOAT'
#     return t

# 에러 처리
def t_error(t):
    # print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()