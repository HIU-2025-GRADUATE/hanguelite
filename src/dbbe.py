import csv, os, random, time, logging
from src.gdbm import *
from src.constant import MASTER_NAME, SQLITE_OK, SQLITE_READONLY, SQLITE_PERM, SQLITE_BUSY
from src.util import *

logging.basicConfig(level=logging.DEBUG)

class BeFile:
    def __init__(self, writeable, zName):
        # 실제 파일명
        self.zName = zName
        # 파일 객체 (csv.reader / csv.write 객체)
        self.dbf = None
        # 참조 횟수 (참조된? 참조중인?)
        self.nRef = 1
        # 종료 시 삭제 여부
        self.delOnClose = False
        # write를 위해 open 되었는지
        self.writeable = writeable
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
        self.pOpen: BeFile = None
        # self.rc4 = rc4init()

        # 열려있는 temporary file 목록
        self.apTemp = list()

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
    
    # void sqliteDbbeCloseTempFile(Dbbe *pBe, FILE *f)
    # Vdbe 클래스 내부의 mutable list Vdbe.apList에 접근하기 위해 인터페이스 수정
    # openTempFile로 열었던 temporary file을 close
    def closeTempFile(self, apList, idx):
        for i in range(len(self.apTemp)):
            if self.apTemp[i] == apList[idx]:
                absPath = os.path.abspath(apList[idx].name)
                self.apTemp[i].close()
                self.apTemp[i] = 0
                apList[idx].close()
                apList[idx] = 0
                os.unlink(absPath)
                break

    # int sqliteDbbeOpenTempFile(Dbbe *pBe, FILE **ppFile)
    # Vdbe 클래스 내부의 mutable list Vdbe.apList에 접근하기 위해 인터페이스 수정
    # temporary 파일 open, 종료 시에 반드시 삭제되어야함
    def openTempFile(self, apList, idx):
        rc = SQLITE_OK

        i=0
        for j in range(0, len(self.apTemp)):
            if self.apTemp[j]==0:
                i=j
                break

        if i >= len(self.apTemp):
            self.apTemp.append(0)

        while True:
            randNum = ''.join(str(random.randint(0, 9)) for _ in range(16))
            zFile = "_temp_file_"+randNum
            if zFile not in os.listdir(self.zDir):
                break

        zFile = os.path.join(self.zDir, zFile)
        apList[idx] = open(zFile, 'w', encoding='utf-8')
        self.apTemp[i] = apList[idx]

        if self.apTemp == 0:
            rc = SQLITE_ERROR

        return rc
        
    
    # static char *sqliteFileOfTable(Dbbe *pBe, const char *zTable)
    # SQL table 이름 혹은 인덱스 값에 해당하는 file 이름으로 변환함
    def fileOfTable(self, zTable):
        fileList = os.listdir(self.zDir)
        if zTable+'.dat' in fileList:
            zFile = os.path.join(self.zDir, zTable)
        else:
            zFile = None
        return zFile

    # 테이블 명이 zTable에 해당하는 파일을 디스크에서 삭제
    def dropTable(self, zTable):
        zFile = self.fileOfTable(zTable)
        if zFile is None:
            return
        for ext in ['.bak', '.dat', '.dir']:
            os.unlink(zFile + ext)
        del zFile

class DbbeCursor:
    def __init__(self):
        # 이 커서가 포함된 DB
        self.pBe: Dbbe = None
        # 이 table의 실제 파일
        self.pFile: BeFile = None
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
        # print(f"close file {self.pFile.zName}")
        self.pFile.nRef -= 1
        if self.pFile.nRef <= 0:
            try:
                if self.pFile.dbf:
                    self.pFile.dbf.close()
            except Exception as e:
                print(e)
            # BeFile 객체의 앞뒤 연결 링크 삭제
            if self.pFile.pPrev:
                self.pFile.pPrev.pNext = self.pFile.pNext
            else:
                self.pBe.pOpen = self.pFile.pNext
            if self.pFile.pNext:
                self.pFile.pNext.pPrev = self.pFile.pPrev

            if self.pFile.delOnClose:
                logging.info(f"Remove File : {self.pFile.zName}")
                os.remove(self.pFile.zName)


    def openCursor(self, pBe: Dbbe, zTable: str, writeable=False):
        zFile = self.__getFileNameOfTable(pBe.zDir, zTable)
        pFile = self.__findExistsCursor(pBe, zFile)
        rc = SQLITE_OK

        if not pFile: # table 경로에 대해 기존 커서가 없다면
            fileMode = "c" if writeable else "w"
            pFile = BeFile(writeable, zFile)

            if zFile: # 테이블 이름이 존재한다면 -> 이 테이블에 대한 커서 열기
                if (not writeable) or pBe.write:
                    pFile.dbf = gdbm_open(zFile, fileMode)
                else:
                    pFile.dbf = None
            else:
                # 랜덤 테이블 이름 생성하고, (위에서 미리 해둠) 해당 파일명의 커서 생성
                pFile.dbf = gdbm_open(zFile, fileMode)
                pFile.delOnClose = True

            # 파일 연결 리스트 세팅
            if pBe.pOpen:
                pBe.pOpen.pPrev = pFile
            pFile.pNext = pBe.pOpen
            pBe.pOpen = pFile

            if pFile.dbf is None:
                if not writeable and not os.path.exists(zFile):
                    # 읽기 모드로 실행했는데, 실제 파일이 없는 경우는 상관없다. (파일의 지연 생성)
                    rc = SQLITE_OK
                elif not pBe.write:
                    rc = SQLITE_READONLY
                elif not os.access(zFile, os.R_OK | os.W_OK):
                    rc = SQLITE_PERM
                else:
                    rc = SQLITE_BUSY

        else: # pFile 커서가 이미 존재
            pFile.nRef += 1
            if writeable and not pFile.writeable:
                rc = SQLITE_READONLY

        # ppCursr에 DbbeCursor 할당
        self.pBe = pBe
        self.pFile = pFile
        self.readPending = False
        self.needRewind = True

        if rc != SQLITE_OK:
            self.closeCursor()

        return rc
    
    def new(self):
        if self.pFile == None or self.pFile.dbf == None: return 1
        while 1:
            random.seed(time.time())
            iKey = f"{random.getrandbits(64):016x}"
            if gdbm_exists(self.pFile.dbf, iKey): continue
            break
        return iKey
    
    def put(self, key, data):
        if self.pFile == 0 or self.pFile.dbf == 0:
            return "SQLITE_ERROR"
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

    def readData(self, offset):
        if self.readPending and self.pFile and self.pFile.dbf:
            self.data = gdbm_fetch(self.pFile.dbf, self.key)
            self.readPending = False
        if offset<0 or offset>=len(self.data): return ''
        return self.data[offset]
    
    # src/dbbe.c
    # char *sqliteDbbeReadKey(DbbeCursor *pCursr, int offset)
    # 파이썬에서 구현 시 offset이 필요없어서 default를 0으로 세팅
    def readKey(self, offset=0):
        # if offset<0 or offset>=len(self.data): return ''
        return self.key

    def fetch(self, key):
        self.key = key
        self.data = gdbm_fetch(self.pFile.dbf, key)
        # (TODO) 원본 코드에서는 pCursr->data.dptr!=0 으로 돼있음
        return (self.data!=None)

    def test(self, key):
        return gdbm_exists(self.pFile.dbf, key)

    # src/dbbe.c
    # int sqliteDbbeDelete(DbbeCursor *pCursr, int nKey, char *pKey)
    def delete(self, key):
        self.key = None
        self.data = None
        rc = gdbm_delete(self.pFile.dbf, key)
        return rc

    def __getFileNameOfTable(self, directory: str, tableName: str):
        if tableName:
            return os.path.join(directory, tableName)
        # TODO : 임시 파일 이름 랜덤 생성
        return os.path.join(directory, "temp_file")

    def __findExistsCursor(self, pBe: Dbbe, fileName: str):
        """
        :param pBe: 현재 데이터베이스의 파일 관리 객체
        :param fileName: 검색할 파일명 (전체 경로)
        :return: 파일 커서, 파일이 없다면 None 반환
        """
        pFile: BeFile = pBe.pOpen
        while pFile and pFile.zName != fileName:
            pFile = pFile.pNext

        return pFile


if __name__ == "__main__":
    c1 = DbbeCursor()
    c1.openCursor(Dbbe(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'), True), "tableA")
    c2 = DbbeCursor()
    c2.openCursor(Dbbe(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'), True), "tableB")

    c1.closeCursor()
    c2.closeCursor()
    pCursor = DbbeCursor()
    pCursor.openCursor(Dbbe(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db'), False), "tableA")
    for _ in range(7):
        pCursor.nextKey()
        print(pCursor.readData(1))
