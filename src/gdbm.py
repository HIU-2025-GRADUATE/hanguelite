import csv, os, dbm
from io import TextIOWrapper
import ast

GDBM_REPLACE = 0
GDBM_INSERT = 1

def gdbm_store(dbf: TextIOWrapper, key, data: list, mode=GDBM_REPLACE):
    dbf[key] = str(data).encode('utf-8')

def gdbm_open(filePath, mode):
    try:
        # print("oepn", filePath, mode)
        return dbm.open(filePath, mode)
    except dbm.error as e:
        if "db file doesn't exist" in str(e):
            # 원래 gdbm 은 파일이 없을 때 null 을 반환함
            print(e)
            return None
        else:
            raise e

def gdbm_fetch(dbf, key):
    return ast.literal_eval(dbf[key].decode('utf-8'))
    # return eval(dbf[key].decode('utf-8'))

def gdbm_exists(dbf, key):
    return (key in dbf.keys())
    
def gdbm_firstKey(dbf):
    try:
        keys = dbf.keys()
        return keys[0] if keys else None
    except Exception as e:
        print(e)
        return None
    
def gdbm_nextKey(dbf, key):
    keys = dbf.keys()
    for i in range(len(keys)):
        if keys[i] == key:
            if i+1 == len(keys):
                return None
            else:
                return keys[i+1]

def gdbm_delete(dbf, key):
    if not key in dbf.keys():
        return
    del dbf[key]

if __name__ == "__main__":
    # path = '/'.join(os.path.abspath(__file__).split("\\")[:-1])+'/'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db')
    print(os.path.join(path, 'student_test'))
    dbf = gdbm_open(os.path.join(path, 'student_test'), "c")
    # gdbm_store(dbf, 'e3f2cc4aaf371618', ['권 찬',26,4], GDBM_REPLACE)
    # gdbm_store(dbf, '84f05dd77fca94f5', ['김 태연',26,4], GDBM_REPLACE)
    # gdbm_store(dbf, 'e79992d46e467582', ['유 호윤',26,4], GDBM_REPLACE)
    currKey = gdbm_firstKey(dbf)
    print(currKey, gdbm_fetch(dbf, currKey))
    currKey = gdbm_nextKey(dbf, currKey)
    print(currKey, gdbm_fetch(dbf, currKey))
    currKey = gdbm_nextKey(dbf, currKey)
    print(currKey, gdbm_fetch(dbf, currKey))