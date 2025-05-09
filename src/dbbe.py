import csv, os, random, time
from src.gdbm import *
from src.constant import MASTER_NAME

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

class Dbbe:
    def __init__(self, databaseName: str, writeFlag: bool):
        """ dbbe.c : sqliteDbbeOpen() 198 ~ 204"""
        # DB를 저장하는 디렉토리
        self.zDir = databaseName
        
        # write 권한이 있는지
        self.write = writeFlag
        # 열린 파일 리스트 (BeFile 끼리의 연결 리스트)
        self.pOpen = None
        # self.rc4 = rc4init()

    def __del__(self):
        del self.zDir
        del self.write
        del self.pOpen

    @staticmethod
    def open(databaseName, writeFlag, createFlag):
        """dbbe.c : sqliteDbbeOpen()"""
        if not writeFlag:
            createFlag = False

        if not os.path.exists(databaseName):
            if createFlag:
                os.makedirs(databaseName, mode=0o750)
            if not os.path.exists(databaseName):
                if createFlag:
                    raise Exception(f"can't find or create directory \"{databaseName}\".\"")
                else:
                    raise Exception(f"can't find directory \"{databaseName}\".")

        if not os.path.isdir(databaseName):
            raise Exception(f"not a directory: \"{databaseName}\"")

        # TODO : 데이터베이스 폴더 쓰기 권한 체크
        """
        if( access(zName, writeFlag ? (X_OK|W_OK|R_OK) : (X_OK|R_OK)) ){
            sqliteSetString(pzErrMsg, "access permission denied", 0);
            return 0;
          }
        """

        # TODO : 마스터 테이블 접근 권한 체크
        """
        zMaster = databaseName + "/" + MASTER_NAME + ".tbl"
        # if (stat(zMaster, & statbuf) == 0
        #         & & access(zMaster, writeFlag ? (W_OK | R_OK): R_OK) != 0 ){
        #     sqliteSetString(pzErrMsg, "access permission denied for ", zMaster, 0);
        # sqliteFree(zMaster);
        # return 0;
        # }
        """

        return Dbbe(databaseName, writeFlag)

class DbbeCursor:
    def __init__(self):
        # 이 커서가 포함된 DB
        self.pBe: Dbbe
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

    def open(self, zName=0, writeFlag=0, createFlag=0, pzErrMsg=0):
        if not writeFlag: createFlag=0
        if createFlag: os.mkdir(zName)
        if not os.path.isdir(zName): return 0

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
        # (TODO) writeable==True 이면 쓸 수 writer 추가
        # writeable==False 면 읽기 전용
        # (ForTest) csv 파일을 읽도록 만들었음
        if not writeable:
            self.pFile.dbf = gdbm_open(os.path.join(pBe.zDir, zFile)+".csv", "r+")
        else:
            self.pFile.dbf = gdbm_open(os.path.join(pBe.zDir, zFile)+".csv", "w+")

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
    
    def new(self):
        if self.pFile == None or self.pFile.dbf == None: return 1
        while 1:
            random.seed(time.time())
            iKey = f"{random.getrandbits(64):016x}"
            if gdbm_exists(self.pFile.dbf, iKey): continue
            break
        return iKey
    
    def put(self, key, data):
        if self.pFile==0 or self.pFile.dbf==0: return "SQLITE_ERROR"
        print(key, data)
        gdbm_store(self.pFile.dbf, key, data, GDBM_REPLACE)

    def nextKey(self):
        if self.pFile==0 or self.pFile.dbf==0:
            self.readPending = False
            return 0
        if self.needRewind:
            nextKey = gdbm_firstKey(self.pFile.dbf)
            self.needRewind = False
        else:
            nextKey = gdbm_nextKey(self.pFile.dbf, self.key)

        self.key = nextKey
        if nextKey == None:
            self.needRewind = True
            # (TODO) readPending = True 일때 안읽은거 아닌가..?
            self.readPending = False
            rc = 0
        else:
            self.readPending = True
            rc = 1
        return rc
    
    def rewind(self):
        self.needRewind = 1

    # (TODO) readKey 파트 만들어야됌
    def readData(self, offset):
        if self.readPending and self.pFile and self.pFile.dbf:
            self.data = gdbm_fetch(self.pFile.dbf, self.key)
            self.readPending = False
        if offset<0 or offset>=len(self.data): return ''
        return self.data[offset]


if __name__ == "__main__":
    pCursor = DbbeCursor()
    pCursor.openCursor(Dbbe(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'), False), "tableA")
    for _ in range(7):
        pCursor.nextKey()
        print(pCursor.readData(1))
