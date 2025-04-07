import ply.yacc as yacc
from myLexer import tokens  # lex에서 정의한 토큰들을 임포트
from src.select import *
from sqliteInt import Parse

# 전역 파서 컨텍스트 등 (예: pParse, SRT_Callback 등)
# pParse, SRT_Callback, sqliteExec, sqliteSelect, sqliteSelectDelete,
# sqliteSelectNew, sqliteIdListAppend 등의 함수가 이미 구현되어 있다고 가정

def p_input(p):
    """input : cmdlist"""
    p[0] = p[1]

def p_cmdlist(p):
    """cmdlist : ecmd"""
    p[0] = p[1]

def p_ecmd(p, pParse): # parser.parse 함수 호출 시 extra_args 라는 매개변수로 Parse 객체 넘기면 여기서 받아서 사용 가능
    """ecmd : cmd"""
    # Execute the command.
    sqliteExec(pParse)
    p[0] = p[1]

def p_cmd(p, pParse):
    """cmd : select"""
    # Execute the SELECT statement with callback and delete the select structure.
    sqliteSelect(pParse, p[1], SRT_Callback, 0)
    sqliteSelectDelete(p[1])
    p[0] = p[1]

def p_select(p):
    """select : oneselect"""
    p[0] = p[1]

def p_oneselect(p):
    """oneselect : TK_SELECT selcollist from"""
    # Create a new SELECT structure using the parsed select list and from clause.
    p[0] = sqliteSelectNew(p[2], p[3], 0, 0, 0, 0, 0)

def p_selcollist_star(p):
    """selcollist : TK_STAR"""
    # When a '*' is encountered, it is represented by 0.
    p[0] = 0

def p_from(p):
    """from : TK_FROM seltablist"""
    p[0] = p[2]

def p_stl_prefix_empty(p):
    """stl_prefix :"""
    # Empty production for stl_prefix, return 0.
    p[0] = 0

def p_seltablist(p):
    """seltablist : stl_prefix id"""
    # Append the identifier to the prefix list.
    p[0] = sqliteIdListAppend(p[1], p[2])

def p_id(p):
    """id : TK_ID"""
    # For a simple identifier, return its string.
    p[0] = p[1]

def p_error(p):
    print("Syntax error in input!", p)

# Build the parser
parser = yacc.yacc()