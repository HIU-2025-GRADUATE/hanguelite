from flask import Flask, render_template, request, jsonify, redirect, url_for # redirect, url_for 추가
import time # time 모듈도 추가 (방명록 타임스탬프용)

app = Flask(__name__)

# --- 가짜 데이터베이스 ---
MOCK_SCHEMA = {
    "users": {
        "cols": ["id", "name", "email", "created_at"],
        "rows": "1.2k rows"
    },
    "orders": {
        "cols": ["id", "user_id", "total", "status"],
        "rows": "850 rows"
    },
    "products": {
        "cols": ["id", "name", "price", "category"],
        "rows": "340 rows"
    },
    "categories": {
        "cols": ["id", "name", "description"],
        "rows": "25 rows"
    },
    "order_items": {
        "cols": ["id", "order_id", "product_id", "quantity"],
        "rows": "2.3k rows"
    }
}

MOCK_DB = {
    "users": [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2024-01-10"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2024-01-11"},
        {"id": 3, "name": "Mike Johnson", "email": "mike@example.com", "created_at": "2024-01-12"},
    ],
    "products": [
        {"id": 101, "name": "Laptop", "price": 1200, "category": 1},
        {"id": 102, "name": "Mouse", "price": 50, "category": 2},
    ],
    "join_query_result": [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "orders": 15},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "orders": 12},
        {"id": 3, "name": "Mike Johnson", "email": "mike@example.com", "orders": 8},
        {"id": 4, "name": "Sarah Wilson", "email": "sarah@example.com", "orders": 7},
        {"id": 5, "name": "David Brown", "email": "david@example.com", "orders": 6},
        {"id": 6, "name": "Lisa Davis", "email": "lisa@example.com", "orders": 5},
        {"id": 7, "name": "Tom Miller", "email": "tom@example.com", "orders": 4},
        {"id": 8, "name": "Amy Taylor", "email": "amy@example.com", "orders": 3},
        {"id": 9, "name": "Chris Lee", "email": "chris@example.com", "orders": 2},
        {"id": 10, "name": "Emma White", "email": "emma@example.com", "orders": 1},
    ]
}
# --- (가짜 데이터 끝) ---


@app.route('/')
def index():
    """메인 페이지 렌더링. 테이블 스키마 정보를 전달합니다."""
    return render_template('index.html', schema=MOCK_SCHEMA)

@app.route('/api/query', methods=['POST'])
def handle_query():
    """SQL 쿼리 요청을 처리합니다."""
    data = request.get_json()
    
    # [수정됨] .rstrip(';') 을 추가해 쿼리 끝의 세미콜론을 제거합니다.
    query = data.get('query', '').strip().rstrip(';').lower()

    # 쿼리 실행 시뮬레이션을 위한 딜레이
    time.sleep(0.5) 

    # 이미지의 JOIN 쿼리 흉내
    if "count(o.id) as order_count" in query:
        results = MOCK_DB["join_query_result"]
        return jsonify({"results": results, "count": len(results)})

    elif query == "select * from users":
        results = MOCK_DB["users"]
        return jsonify({"results": results, "count": len(results)})
    
    elif query == "select * from products":
        results = MOCK_DB["products"]
        return jsonify({"results": results, "count": len(results)})

    else:
        # 일치하는 쿼리가 없는 경우
        return jsonify({"error": "지원하지 않는 쿼리입니다. (가짜 데이터이므로 일부 쿼리만 동작합니다)"}), 400
    
# --- 방명록 기능 (간단한 예시) ---
GUESTBOOK_ENTRIES = [] # 방명록 게시물 저장용 리스트 (서버 재시작시 초기화)

@app.route('/guestbook')
def guestbook_index():
    """방명록 페이지를 렌더링합니다."""
    return render_template('guestbook.html', entries=GUESTBOOK_ENTRIES)

@app.route('/guestbook/submit', methods=['POST'])
def guestbook_submit():
    """방명록 게시물을 제출합니다."""
    name = request.form.get('name', 'Anonymous')
    message = request.form.get('message', '')
    if name and message:
        GUESTBOOK_ENTRIES.append({'name': name, 'message': message, 'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")})
    return redirect(url_for('guestbook_index')) # 방명록 페이지로 리디렉션

if __name__ == '__main__':
    app.run(debug=True)