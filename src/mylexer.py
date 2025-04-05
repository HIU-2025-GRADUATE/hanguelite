import ply.lex as lex

# 토큰 이름 목록: parse.y에서 사용되는 토큰들과 SQLite의 tokenize.c에 있는 키워드들
tokens = (
    'TK_SELECT', 'TK_FROM', 'TK_STAR', 'TK_ID', 'TK_DOT', 'TK_COLUMN', 'TK_IN'
)

# 예약어 사전 (대소문자 무시 처리)
reserved = {
    'SELECT': 'TK_SELECT',
    'FROM': 'TK_FROM',
    'IN' : 'TK_IN'
}

# 정규표현식 규칙
t_TK_STAR       = r'\*'
t_TK_DOT        = r'\.'
t_TK_ignore     = ' \t\n'

# 식별자 처리: 예약어와 일반 ID 구분
def t_ID(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    # 키워드인지 확인 (대문자로 비교)
    upper_val = t.value.upper()
    if upper_val in reserved:
        t.type = reserved[upper_val]
    else:
        t.type = 'TK_ID'
    return t

# 에러 처리
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()