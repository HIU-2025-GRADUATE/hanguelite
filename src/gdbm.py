import csv, os, dbm
from io import TextIOWrapper

GDBM_REPLACE = 0
GDBM_INSERT = 1

def gdbm_store(dbf: TextIOWrapper, key, data: list, mode=GDBM_REPLACE):
    dbf[key] = str(data).encode('utf-8')
    # record = [key] + data
    # dbf.write(",".join(map(str, record)) + '\n')
    # dbf.flush()

def gdbm_open(filePath, mode):
    return dbm.open(filePath, mode)

def gdbm_fetch(dbf, key):
    return eval(dbf[key].decode('utf-8'))
    # dbf.seek(0)
    # db = {l[0]:l[1:] for l in csv.reader(dbf)}
    # return db[key]

def gdbm_exists(dbf, key):
    return (key in dbf.keys())
    # dbf.seek(0)
    # db = {l[0]:l[1:] for l in csv.reader(dbf)}
    # if key in db: 
    #     del db
    #     return True
    # else:
    #     del db
        # return False
    
def gdbm_firstKey(dbf):
    try:
        return dbf.items()[0][0]
    except:
        return None
    # dbf.seek(0)
    # db = {l[0]:l[1:] for l in csv.reader(dbf)}
    # if len(db)==0: key = None
    # else: key = next(iter(db))
    # return key
    
def gdbm_nextKey(dbf, key):
    keys = dbf.keys()
    for i in range(len(dbf.items())):
        if keys[i] == key:
            if i+1 == len(dbf.items()):
                return None
            else:
                return keys[i+1]

    # return dbf.nextKey(key)
    # dbf.seek(0)
    # db = {l[0]:l[1:] for l in csv.reader(dbf)}
    # keys = list(db.keys())
    # idx = keys.index(key)
    
    # if idx+1 < len(keys): return keys[idx+1]
    # else: return None

def gdbm_delete(dbf, key):
    if not key in dbf.keys():
        return
    del dbf[key]

if __name__ == "__main__":
    path = '/'.join(os.path.abspath(__file__).split("\\")[:-1])+'/'
    dbf = gdbm_open(path+'student', "c")
    # gdbm_store(dbf, 'e3f2cc4aaf371618', ['권 찬',26,4], GDBM_REPLACE)
    # gdbm_store(dbf, '84f05dd77fca94f5', ['김 태연',26,4], GDBM_REPLACE)
    # gdbm_store(dbf, 'e79992d46e467582', ['유 호윤',26,4], GDBM_REPLACE)
    currKey = gdbm_firstKey(dbf)
    print(currKey, gdbm_fetch(dbf, currKey))
    currKey = gdbm_nextKey(dbf, currKey)
    print(currKey, gdbm_fetch(dbf, currKey))
    currKey = gdbm_nextKey(dbf, currKey)
    print(currKey, gdbm_fetch(dbf, currKey))