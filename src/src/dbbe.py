import csv, os

class BeFile:
    def __init__(self):
        # 실제 파일명
        self.zName = None
        # 파일 객체 (csv.reader / csv.write 객체)
        self.dbf = None
        # 참조 횟수 (참조된? 참조중인?)
        self.nRef = 0
        # 종료 시 삭제 여부
        self.delOnClose = False
        # write를 위해 open 되었는지
        self.writeable = False
        # 열린 파일 리스트 중 이전/다음 파일 (BeFile 객체, 연결 리스트)
        self.pPrev = None
        self.pNext = None

    def __del__(self):
        del self.zName
        del self.dbf
        del self.nRef
        del self.delOnClose
        del self.writeable
        del self.pPrev
        del self.pNext

class rc4:
    def __init__(self):
        self.i = 0
        self.j = 0
        self.s = None

    def __del__(self):
        del self.i
        del self.j
        del self.s

class Dbbe:
    def __init__(self):
        # DB를 저장하는 디렉토리
        # self.zDir = None
        # (ForTest) 현재 디렉토리 절대경로를 가리키게 작성
        self.zDir = '/'.join(os.path.abspath(__file__).split("\\")[:-1])+'/'
        
        # write 권한이 있는지
        self.write = False
        # 열린 파일 리스트 (BeFile 끼리의 연결 리스트)
        self.pOpen = None
        # rc 클래스의 인스턴스
        self.rc4 = rc4()

    def __del__(self):
        del self.zDir
        del self.write
        del self.pOpen
        del self.rc4

class DbbeCursor:
    def __init__(self):
        # 이 커서가 포함된 DB
        self.pBe = Dbbe()
        # 이 table의 실제 파일
        self.pFile = BeFile()
        # 최근에 사용한 key
        self.key = None
        # 최근에 사용한 data
        self.data = None
        # Next key should be the first
        self.needRewind = True
        # The fetch hasn't actually been done yet
        self.readPending = False

    def __del__(self):
        del self.pBe
        del self.pFile
        del self.key
        del self.data
        del self.needRewind
        del self.readPending

    def closeCursor(self):
        if self==0: return
        self.pFile.nRef -= 1
        if self.pFile.nRef <= 0:
            if self.pFile.dbf: self.pFile.dbf.close()
            # BeFile 객체의 앞뒤 연결 링크 삭제
            if self.pFile.pPrev: self.pFile.pPrev.pNext = self.pFile.pNext
            else: self.pBe.pOpen = self.pFile.pNext
            if self.pFile.pNext: self.pFile.pNext.pPrev = self.pFile.pPrev
        self = 0
        return

    def openCursor(self, pBe, zFile, writeable=False):
        # (ToDo) writeable==True 이면 쓸 수 writer 추가
        # writeable==False 면 읽기 전용
        # (ForTest) csv 파일을 읽도록 만들었음
        if not writeable:
            self.pFile.dbf = open(pBe.zDir+zFile+".csv", "r", encoding='utf-8')

        # pFile 객체 변수를 세탕하고 pBe.pOpen에 대입
        self.pFile.writeable = writeable
        self.pFile.zName = zFile
        self.pFile.nRef = 1
        self.pFile.pPrev = 0
        if pBe.pOpen: pBe.pOpen.pPrev = self.pFile
        self.pFile.pNext = pBe.pOpen
        pBe.pOpen = self.pFile

        # ppCursr에 DbbeCursor 할당
        self.pBe = pBe
        return