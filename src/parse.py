import ply.yacc as yacc
from src.tokenizer import tokens  # lex에서 정의한 토큰들을 임포트
from src.select import *

# 전역 파서 컨텍스트 등 (예: pParse, SRT_Callback 등)
# pParse, SRT_Callback, sqliteExec, sqliteSelect, sqliteSelectDelete,
# sqliteSelectNew, sqliteIdListAppend 등의 함수가 이미 구현되어 있다고 가정

pParse = None

def set_parse_object(parse_obj):
    global pParse
    pParse = parse_obj

def p_input(p):
    """input : cmdlist"""
    p[0] = p[1]

def p_cmdlist(p):
    """cmdlist : ecmd"""
    p[0] = p[1]

def p_ecmd(p): 
    """ecmd : cmd"""
    # Execute the command.
    global pParse
    sqliteExec(pParse) 
    p[0] = p[1]

def p_cmd(p):
    """cmd : select"""
    # Execute the SELECT statement with callback and delete the select structure.
    global pParse
    sqliteSelect(pParse, p[1], SRT_Callback, 0)
    sqliteSelectDelete(p[1])
    p[0] = p[1]

def p_select(p):
    """select : oneselect"""
    p[0] = p[1]

def p_oneselect(p):
    """oneselect : TK_SELECT selcollist from"""
    # Create a new SELECT structure using the parsed select list and from clause.
    p[0] = sqliteSelectNew(p[2], p[3], None, None, None, None, None)

def p_selcollist_star(p):
    """selcollist : TK_STAR"""
    # When a '*' is encountered, it is represented by 0.
    p[0] = None

def p_from(p):
    """from : TK_FROM seltablist"""
    p[0] = p[2]

def p_stl_prefix_empty(p):
    """stl_prefix :"""
    # Empty production for stl_prefix, return 0.
    p[0] = None

def p_seltablist(p):
    """seltablist : stl_prefix id"""
    # Append the identifier to the prefix list.
    p[0] = sqliteIdListAppend(p[1], p[2])

def p_id(p):
    """id : TK_ID"""
    # For a simple identifier, return its string.
    token = Token()
    token.z = p[1]
    token.n = len(token.z)
    p[0] = token

def p_error(p):
    print("Syntax error in input!", p)

# Build the parser
parser = yacc.yacc()