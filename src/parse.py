import ply.yacc as yacc
from src.build import *
from sql_struct import Parse
from tokenizer import tokens

def p_input_commands(p):
    'input : cmdlist'
    if parse.error_msg:
        print(parse.error_msg)

def p_commands_command_end(p):
    'cmdlist : ecmd'

def p_command_end_command(p):
    'ecmd : cmd'
    sql_exec(parse)  # Execute SQL

"""
    CREATE TABLE
"""
def p_command_create(p):
    'cmd : create_table create_table_args'

def p_create_table(p):
    'create_table : CREATE TABLE id'
    # test
    parse.error_msg = f"create table named : {p[3]}"
    sql_start_table(parse, p[3])

def p_create_table_args(p):
    'create_table_args : LP columnlist RP' # constraint 는 아직 고려 안함
    sql_end_table(parse)

def p_columnlist_multiple(p):
    'columnlist : columnlist COMMA column'

def p_columnlist_single(p):
    'columnlist : column'

def p_column(p):
    'column : columnid type' # constraint 는 아직 고려 안함

def p_columnid(p):
    'columnid : id'
    sql_add_column(parse, p[1])
    p[0] = p[1]

def p_type(p):
    'type : typename'

def p_typename(p):
    'typename : id'

def p_id_from_string(p):
    'id : STRING'
    p[0] = p[1]

def p_id_from_ID(p):
    'id : ID'
    p[0] = p[1]

def p_error(p):
    if p:
        print(f"[SYNTAX ERROR] Unexpected token: {p.type} ({p.value}) at line {p.lineno}")
    else:
        print('Syntax error in input!')

parse = Parse.empty()
parser = yacc.yacc(debug=True)