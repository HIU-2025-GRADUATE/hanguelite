import ply.lex as lex

reserved = {
    'CREATE' : 'CREATE',
    'TABLE' : 'TABLE',
}

tokens = (
    'ID',
    'STRING',
    'LP',
    'RP',
    'COMMA',
) + tuple(reserved.values())

t_LP = r'\('
t_RP = r'\)'
t_COMMA = r','

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.upper(), 'STRING')
    return t

def t_STRING(t):
    r'[a-zA-Z]+'
    t.type = reserved.get(t.value.upper(), 'STRING')
    return t

t_ignore = ' \t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()