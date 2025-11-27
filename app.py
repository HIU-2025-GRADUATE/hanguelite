from flask import Flask, render_template, request, jsonify, redirect, url_for
import time
import re

# main 함수
from src.parse import parser, set_parse_object
from src.sqliteInt import Parse, sqlite
from src.dto.selectQueryDTO import *
from src.dto.response import Response
import os
import copy

def preprocess_korean_sql(sql: str) -> str:
    rules: list[tuple[re.Pattern, callable]] = [
        (re.compile(r'(으로|로)\s*묶고'),
         lambda m: f'{m.group(1)}묶고'),
        (re.compile(r'(으로|로)\s*정렬해서'),
         lambda m: f'{m.group(1)}정렬해서'),
        (re.compile(r'일\s*때'),
         lambda m: '일때'),
    ]

    for pattern, repl in rules:
        sql = pattern.sub(repl, sql)

    return sql

def runParser(parse: Parse, sql: str):
    set_parse_object(parse)
    parser.parse(sql, debug=False)

def execute_sql(db, sql: str):
    try:
        dto.clearDto()
        parse = Parse(db)
        check = ['select', 'insert', 'update', 'delete', 'create', 'drop']
        s = sql.split()

        if s[0].lower() not in check:
            sql = s[-1] + " " + " ".join(s[:-1])
            sql = preprocess_korean_sql(sql)

        runParser(parse, sql)

        if dto.flag:
            return Response(200, None, dto)
        else:
            return Response(201, None, dto)

    except Exception as e:
        raise e
        return Response(400, str(e), None)

def extend_logs(old, new, sql):
    old.append(f"SQL: {sql}")
    old.append('--------------------')
    old.extend(new)
    old.append("=================================================================")
    return old

def parse_col_info(raw):
    tmp = raw.strip().split(' ')
    return f"{tmp[0]} ({tmp[1]})"

app = Flask(__name__)
db = sqlite.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'))

from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)


@app.route('/')
def index():
    global db
    debugs = list()

    s = 'select * from hqlite_master;'
    execute_sql(db, s)
    data = {'column_names': copy.deepcopy(dto.columnNames), 'rows': copy.deepcopy(dto.rows)}
    debugs = extend_logs(debugs, dto.logs, s)

    tables = dict()
    for rows in data['rows']:
        if rows[0] == 'table':
            line = rows[3].split('(')[1].split(')')[0]
            tables[rows[1]] = dict()
            tables[rows[1]]['cols'] = list(map(lambda x: parse_col_info(x), line.split(',')))
            # tables[rows[1]]['cols'] = list(map(lambda x: x.strip().split(' ')[0], line.split(',')))

            sql = 'select count(*) from ' + rows[1]
            execute_sql(db, sql)
            data_rows = copy.deepcopy(dto.rows)
            debugs = extend_logs(debugs, dto.logs, sql)
            dto.clearDto()
            
            if len(data_rows)==0:
                tables[rows[1]]['rows'] = '0 rows'
            else:
                tables[rows[1]]['rows'] = f'{data_rows[0][0]} rows'

            del data_rows
    del data
    # print(debugs)
    
    return render_template('index.html', schema=tables, debugs=debugs)


# SQL 쿼리문 실행
@app.route('/api/query', methods=['POST'])
def handle_query():
    try:
        global db
        debugs = list()
        dto.clearDto()

        """SQL 쿼리 요청을 처리합니다."""
        data = request.get_json()
        raw_query = data.get('query', [])

        query_list = raw_query.split('\n')
        real_query = "\n".join([query_line for query_line in query_list if query_line.strip() != '' and not query_line.strip().startswith('--')])

        print("-----------")
        print("real_query:", '\n'+real_query)
        print("-----------")

        final_response = None
        for query in real_query.split(';'):
            if not query:
                continue
            response: Response = execute_sql(db, query)
            print("response:", response.status, response.data, response.msg)

            if response.status == 400:
                return jsonify({"results": [], "count": '', "debugs": debugs, "msg": response.msg}), 400

            if response.status == 200:
                response_data: SelectQueryDTO = response.data
                data = {'column_names': copy.deepcopy(response_data.columnNames), 'rows': copy.deepcopy(response_data.rows)}
                print("Data:",data)
                debugs = extend_logs(debugs, response_data.logs, query)
                dto.clearDto()

                results = []
                results.append(data['column_names'])
                for line in data['rows']:
                    tmp = dict()
                    for i in range(len(data['column_names'])):
                        tmp[data['column_names'][i]] = line[i]
                    results.append(tmp)

                final_response = (jsonify({"results": results, "count": len(results), "debugs": debugs, "msg": "ok"}), 200)
            elif response.status == 201:
                response_data: SelectQueryDTO = response.data
                debugs = extend_logs(debugs, response_data.logs, query)
                final_response = (jsonify({"results": [], "count": 0, "debugs": debugs, "msg": "ok"}), 201)
            else:
                raise Exception(f"Unknown Response Status: {response.status}")

        return final_response
    except Exception as e:
        print(e)
        return jsonify({"results": [], "count": '', "debugs": debugs, "msg": str(e)}), 500


"""방명록 페이지를 렌더링합니다."""
@app.route('/guestbook')
def guestbook_index():
    try:
        query = 'select * from guestbook'
        response: Response = execute_sql(db, query)
        db_data = {'column_names': copy.deepcopy(dto.columnNames), 'rows': copy.deepcopy(dto.rows)}
        dto.clearDto()

        print(response.status, response.data, response.msg)
        if response.status == 400:
            raise Exception(response.msg)
    
    except:
        query = 'create table guestbook (name varchar, _time timestamp, message varchar);'
        execute_sql(db, query)

        query = 'select * from guestbook'
        execute_sql(db, query)
        db_data = {'column_names': copy.deepcopy(dto.columnNames), 'rows': copy.deepcopy(dto.rows)}
        dto.clearDto()
    
    entries = list()
    for row in db_data['rows']:
        entries.append(dict(zip(['name', 'timestamp', 'message'], row)))

    sorted_entries = sorted(entries, key=lambda x: x['timestamp'])

    return render_template('guestbook.html', entries=sorted_entries)

@app.route('/guestbook/submit', methods=['POST'])
def guestbook_submit():
    global db
    debugs = list()
    """방명록 게시물을 제출합니다."""

    name = request.form.get('name', 'Anonymous')
    message = request.form.get('message', '')
    if name and message:
        with open(f"./guestbook/{time.strftime('%Y%m%d_%H%M%S.txt')}", 'a+') as f:
            f.write(f"{name} : {message}\n")
        query = f"insert into guestbook values ('{name}', '{time.strftime('%Y-%m-%d %H:%M:%S')}', '{message}')"
        print(f"   Query: {query}")
        execute_sql(db, query)
        dto.clearDto()

    return redirect(url_for('guestbook_index')) # 방명록 페이지로 리디렉션

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556)