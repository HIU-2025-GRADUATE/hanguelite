from src.parse import parser, set_parse_object
from src.sqliteInt import Parse, sqlite
import os


def runParser(parse: Parse, sql: str):
    set_parse_object(parse)
    parser.parse(sql, debug=False)

def execute_sql(db, sql):
    parse = Parse(db)
    runParser(parse, sql)


def main():
    db = sqlite.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'))
    while True:
        try:
            s = input('sql > ')
        except EOFError:
            break

        if s:
            execute_sql(db, s)

if __name__ == '__main__':
    main()