from ply import yacc
from src.select import *
from src.tokenizer import tokens

# 전역 파서 컨텍스트 등 (예: pParse, SRT_Callback 등)
# pParse, SRT_Callback, sqliteExec, sqliteSelect, sqliteSelectDelete,
# sqliteSelectNew, sqliteIdListAppend 등의 함수가 이미 구현되어 있다고 가정

pParse: Parse = None

def set_parse_object(parse_obj):
    global pParse
    pParse = parse_obj

def p_input(p):
    """input : cmdlist"""
    p[0] = p[1]
    if pParse.zErrMsg:
        print(pParse.zErrMsg)

def p_cmdlist(p):
    """cmdlist : ecmd"""
    p[0] = p[1]

def p_ecmd(p): 
    """ecmd : cmd"""
    execute(pParse) # Execute the command.
    p[0] = p[1]

"""
    CREATE TABLE
"""
def p_command_create(p):
    """cmd : create_table create_table_args"""  #

def p_create_table(p):
    """create_table : TK_CREATE TK_TABLE id"""  #

    # test
    pParse.zErrMsg = f"create table named : {p[3]}"
    startTable(pParse, p[3])

def p_create_table_args(p):
    """create_table_args : TK_LP columnlist TK_RP"""  # constraint 는 아직 고려 안함
    # p[0] = " ".join(p[1:])
    endTable(pParse, p[0])

def p_columnlist_multiple(p):
    """columnlist : columnlist TK_COMMA column"""
    # p[0] = " ".join(p[1:])

def p_columnlist_single(p):
    """columnlist : column"""
    # p[0] = p[1]

def p_column(p):
    """column : columnid type"""  # constraint 는 아직 고려 안함
    # p[0] = p[1] + " " + p[2]

def p_columnid(p):
    """columnid : id"""
    addColumn(pParse, p[1])
    # p[0] = p[1]

def p_type(p):
    """type : typename"""
    # p[0] = p[1]

def p_typename(p):
    """typename : id"""
    # p[0] = p[1]

def p_id_from_string(p):
    """id : TK_STRING"""
    # p[0] = p[1]

"""
    SELECT
"""
def p_cmd(p):
    """cmd : select"""
    # Execute the SELECT statement with callback and delete the select structure.
    global pParse
    select(pParse, p[1], SRT_Callback, 0)
    p[0] = p[1]

def p_select(p):
    """select : oneselect"""
    p[0] = p[1]

def p_oneselect(p):
    """oneselect : TK_SELECT selcollist from"""
    # Create a new SELECT structure using the parsed select list and from clause.
    p[0] = Select(p[2], p[3], None, None, None, None, 0)

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
    if p[1] is None:
        p[1] = IdList()
    p[1].idListAppend(p[2])
    p[0] = p[1]


def p_id(p):
    """id : TK_ID"""
    # For a simple identifier, return its string.
    p[0] = Token(p[1])

def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Unexpected token: {p.type} ({p.value}) at line {p.lineno}")
    else:
        print('Syntax error in input!')

# Build the parser
parser = yacc.yacc(debug=True)