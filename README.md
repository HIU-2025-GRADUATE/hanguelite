# hanguelite
hanguelite 는 sqlite 1.0 소스코드를 기반으로 한글 SQL 문법을 재정의하여 만든 데이터베이스 입니다.
문자열 처리 편의를 위해 C언어로 작성된 sqlite 1.0 원본 코드를 따라가지 않고, Python 을 사용하여 개발하였습니다.

[유튜브 소개 영상](https://www.youtube.com/watch?v=5NA56h0oAds)   
[시연 사이트](http://hanguelite.everdu.com:5000/)

## 주요 문법
### CREATE
테이블 이름, 컬럼명, 컬럼 타입을 한글로 작성할 수도 있습니다.
- 문법
  ```text
  {테이블 이름} ({컬럼명 컬럼타입}, ...) 테이블을 만들어줘
  ```
- 예시
  ```text
  student (sid int, sname string) 테이블을 만들어줘
  ```

### INSERT
- 문법
  ```text
  {테이블 이름} 테이블에 (value, value, ..) 를 삽입해줘
  ```
- 예시
  ```text
  student 테이블에 (1, "kim") 을 삽입해줘
  ```

### UPDATE
- 문법
  ```text
  {테이블 이름} 테이블에 (value, value, ..) 를 삽입해줘
  ```
- 예시
  ```text
  student 테이블에 (1, "kim") 을 삽입해줘
  ```

### DELETE
- 문법
  ```text
  {테이블 이름} 테이블에 (value, value, ..) 를 삽입해줘
  ```
- 예시
  ```text
  student 테이블에 (1, "kim") 을 삽입해줘
  ```

### DROP
- 문법
  ```text
  {테이블 이름} 테이블에 (value, value, ..) 를 삽입해줘
  ```
- 예시
  ```text
  student 테이블에 (1, "kim") 을 삽입해줘
  ```

### SELECT
- 문법
  ```text
  {테이블 이름} 테이블에 (value, value, ..) 를 삽입해줘
  ```
- 예시
  ```text
  student 테이블에 (1, "kim") 을 삽입해줘
  ```
