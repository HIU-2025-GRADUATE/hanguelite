from ply import yacc
from src.select import *
from src.insert import *
from src.tokenizer import tokens

# 전역 파서 컨텍스트 등 (예: pParse, SRT_Callback 등)
# pParse, SRT_Callback, sqliteExec, sqliteSelect, sqliteSelectDelete,
# sqliteSelectNew, sqliteIdListAppend 등의 함수가 이미 구현되어 있다고 가정

pParse: Parse = None
createQuery: str = ""

precedence = (
    ('left', 'TK_OR'),
    ('left', 'TK_AND'),
    ('right', 'TK_NOT'),
    ('left', 'TK_EQ', 'TK_NE', 'TK_LIKE'),
    ('left', 'TK_GT', 'TK_GE', 'TK_LT', 'TK_LE'),
)

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
    global createQuery

    startTable(pParse, p[3])

    p[0] = " ".join(map(str, p[1:]))
    createQuery = p[0]

def p_create_table_args(p):
    """create_table_args : TK_LP columnlist TK_RP"""  # constraint 는 아직 고려 안함
    global createQuery

    p[0] = " ".join(p[1:])
    createQuery += p[0]
    endTable(pParse, createQuery)

def p_columnlist_multiple(p):
    """columnlist : columnlist TK_COMMA column"""
    p[0] = " ".join(p[1:])

def p_columnlist_single(p):
    """columnlist : column"""
    p[0] = p[1]

def p_column(p):
    """column : columnid type"""  # constraint 는 아직 고려 안함
    p[0] = " ".join(map(str, p[1:]))

def p_columnid(p):
    """columnid : id"""
    addColumn(pParse, p[1])
    p[0] = p[1]

def p_type(p):
    """type : typename"""
    p[0] = p[1]

def p_typename(p):
    """typename : id"""
    p[0] = p[1]

def p_id_from_string(p):
    """id : TK_STRING"""
    p[0] = p[1]

"""
    INSERT
"""
def p_command_insert_value(p):
    """cmd : TK_INSERT TK_INTO id inscollist_opt TK_VALUES TK_LP itemlist TK_RP"""
    targetTable, itemList, colList = str(p[3]), p[7], p[4]
    insert(pParse, targetTable, itemList, None, colList)

def p_command_insert_from_select(p):
    """cmd : TK_INSERT TK_INTO id inscollist_opt select"""
    targetTable, select_info, colList = str(p[3]), p[5], p[4]
    insert(pParse, targetTable, 0, select_info, colList)

def p_ins_col_list_opt_empty(p):
    """inscollist_opt : """
    p[0] = None

def p_ins_col_list_opt(p):
    """inscollist_opt : TK_LP inscollist TK_RP"""
    p[0] = p[2]

def p_ins_col_list(p):
    """inscollist : inscollist TK_COMMA id"""
    idList: IdList = p[1]
    idList.idListAppend(p[3])
    p[0] = idList

def p_ins_col_list_one(p):
    """inscollist : id"""
    idList = IdList()
    idList.idListAppend(p[1])
    p[0] = idList

def p_item_list(p):
    """itemlist : itemlist TK_COMMA item"""
    exprList: ExprList = p[1]
    exprList.exprListAppend(p[3], None)
    p[0] = exprList

def p_item_list_one(p):
    """itemlist : item"""
    exprList = ExprList()
    exprList.exprListAppend(p[1], None)
    p[0] = exprList

def p_item_int(p):
    """item : TK_INTEGER"""
    p[0] = Expr(TK_INTEGER, None, None, Token(str(p[1])))

def p_item_plus_int(p):
    """item : TK_PLUS TK_INTEGER"""
    p[0] = Expr(TK_INTEGER, None, None, Token(p[1]+str(p[2])))

def p_item_minus_int(p):
    """item : TK_MINUS TK_INTEGER"""
    p[0] = Expr(TK_INTEGER, None, None, Token(p[1]+str(p[2])))

# def p_item_float(p):
#     """item : TK_FLOAT"""
#
# def p_item_plus_float(p):
#     """item : TK_PLUS TK_FLOAT"""
#
# def p_item_minus_float(p):
#     """item : TK_MINUS TK_FLOAT"""

def p_item_str(p):
    """item : TK_STRING"""
    p[0] = Expr(TK_STRING, None, None, Token(p[1]))

def p_item_null(p):
    """item : TK_NULL"""
    p[0] = Expr(TK_NULL, None, None, None)

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
    """oneselect : TK_SELECT selcollist from where_opt"""
    # Create a new SELECT structure using the parsed select list and from clause.
    p[0] = Select(p[2], p[3], p[4], None, None, None, 0)

def p_selcollist_star(p):
    """selcollist : TK_STAR"""
    # When a '*' is encountered, it is represented by 0.
    p[0] = None

def p_selcollist(p):
    """selcollist : sclp expr"""
    if p[1] is None:
        p[1] = ExprList()
    p[1].exprListAppend(p[2], None)
    p[0] = p[1]

def p_sclp_comma(p):
    """sclp : selcollist TK_COMMA"""
    p[0] = p[1]

def p_sclp_empty(p):
    """sclp :"""
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

def p_where_opt_empty(p):
    """where_opt :"""
    p[0] = None  

def p_where_opt_expr(p):
    """where_opt : TK_WHERE expr"""
    p[0] = p[2]  

def p_expr_and(p):
    """expr : expr TK_AND expr"""
    p[0] = Expr(TK_AND, p[1], p[3], None, p[2])

def p_expr_or(p):
    """expr : expr TK_OR expr"""
    p[0] = Expr(TK_OR, p[1], p[3], None, p[2])

def p_expr_lt(p):
    """expr : expr TK_LT expr"""
    p[0] = Expr(TK_LT, p[1], p[3], None, p[2])

def p_expr_gt(p):
    """expr : expr TK_GT expr"""
    p[0] = Expr(TK_GT, p[1], p[3], None, p[2])

def p_expr_le(p):
    """expr : expr TK_LE expr"""
    p[0] = Expr(TK_LE, p[1], p[3], None, p[2])

def p_expr_ge(p):
    """expr : expr TK_GE expr"""
    p[0] = Expr(TK_GE, p[1], p[3], None, p[2])

def p_expr_ne(p):
    """expr : expr TK_NE expr"""
    p[0] = Expr(TK_NE, p[1], p[3], None, p[2])

def p_expr_eq(p):
    """expr : expr TK_EQ expr"""
    p[0] = Expr(TK_EQ, p[1], p[3], None, p[2])

def p_expr_like(p):
    """expr : expr TK_LIKE expr"""
    p[0] = Expr(TK_LIKE, p[1], p[3], None, p[2])

def p_expr_integer(p):
    """expr : TK_INTEGER"""
    p[0] = Expr(TK_INTEGER, None, None, Token(p[1]))

def p_expr_float(p):
    """expr : TK_FLOAT"""
    p[0] = Expr(TK_FLOAT, None, None, Token(p[1]))

def p_expr_string(p):
    """expr : TK_STRING"""
    p[0] = Expr(TK_STRING, None, None, Token(p[1]))

def p_expr_id(p):
    """expr : TK_ID"""
    p[0] = Expr(TK_ID, None, None, Token(p[1]))

def p_id(p):
    """id : TK_ID"""
    # For a simple identifier, return its string.
    p[0] = Token(p[1])

def p_expr_not(p):
    """expr : TK_NOT expr"""
    e = Expr(TK_NOT, p[2], None, None)
    e.span = Token(p[1] + " " + p[2].span.z)
    p[0] = e

def p_expr_not_like(p):
    """expr : expr TK_NOT TK_LIKE expr"""
    e1 = Expr(TK_LIKE, p[1], p[4], None, p[2] + " " + p[3])
    e2 = Expr(TK_NOT, e1, None, None)
    e2.span = Token(p[1].span.z + " " + p[2] + " " + p[3] + " " + p[4].span.z)
    p[0] = e2

def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Unexpected token: {p.type} ({p.value}) at line {p.lineno}")
    else:
        print('Syntax error in input!')

# Build the parser
parser = yacc.yacc(debug=True)