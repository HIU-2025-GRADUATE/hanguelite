from src.parse import parser, set_parse_object
from src.sqliteInt import Parse, sqlite
from src.dto.selectQueryDTO import *
from src.dto.response import *
import os
import re
import copy

def runParser(parse: Parse, sql: str):
    set_parse_object(parse)
    parser.parse(sql, debug=False)

def execute_sql(db, sql):
    parse = Parse(db)

    if bool(re.search("[가-힣]", sql)):
        s = sql.split()
        sql = s[-1] + " " + " ".join(s[:-1])
    
    runParser(parse, sql)

def main():
    db = sqlite.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'))
    while True:
        try:
            s = input('sql > ')
            if not s:
                continue
        except EOFError:
            break

        try:
            execute_sql(db, s)
            if dto.getFlag():
                data = {'column_names': copy.deepcopy(dto.columnNames), 'rows': copy.deepcopy(dto.rows)}
                print(data)
                dto.clearDto()
                return Response(200, None, data)
            else:
                return Response(200, None, None)
            

        except Exception as e:
            return Response(400, str(e), None)

if __name__ == '__main__':
    main()