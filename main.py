from src.parse import parser, set_parse_object
from src.sqliteInt import Parse, sqlite
import os


def runParser(parse: Parse, sql: str):
    set_parse_object(parse)
    result = parser.parse(sql, debug=True)
    print(result)

def execute_sql(db, sql):
    parse = Parse(db)
    runParser(parse, sql)


def main():
#     # Test it out
#     data = '''CREATE TABLE test'''
#
#     # Give the lexer some input
#     lexer.input(data)
#
#     # Tokenize
#     while True:
#         tok = lexer.token()
#         if not tok:
#             break  # No more input
#         print(tok)
#
    db = sqlite.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'))
    while True:
        try:
            s = input('sql > ')
        except EOFError:
            break
        if not s: continue

        execute_sql(db, s)

if __name__ == '__main__':
    main()