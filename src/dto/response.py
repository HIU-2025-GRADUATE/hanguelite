from src.dto.selectQueryDTO import SelectQueryDTO


class Response:
    def __init__(self, status, msg, data):
        self.status: int = status # 성공 실패 여부 상태 코드
        self.msg: str = msg # 실패시 에러메세지
        self.data: SelectQueryDTO = data # 성공시 데이터