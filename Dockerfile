# 1. 베이스 이미지
FROM python:3.12-slim

# 2. 작업 디렉토리 생성
WORKDIR /app

# 3. OS 패키지 업데이트 & 필요한 패키지 설치 (선택)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 & 설치
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 전체 복사
COPY . .

# 6. Gunicorn으로 Flask 실행 (포트 5555)
EXPOSE 5555

# Flask 앱 이름(app.py 파일에 있는 변수명)
# 예: app.py 내부에서 app = Flask(__name__) 라면 아래처럼 지정
CMD ["gunicorn", "-b", "0.0.0.0:5555", "app:app"]