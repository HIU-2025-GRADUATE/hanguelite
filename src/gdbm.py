import csv, os

GDBM_REPLACE = 0
GDBM_INSERT = 1

def gdbm_store(dbf=0, key='', data='', mode=0):
    dbf.seek(0)
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    if mode == GDBM_INSERT and key in db:
        return "ERROR"
    db[key]=data
    print(dbf.name)
    with open(os.path.abspath(dbf.name), "w", encoding='utf-8') as f:
        for key in db:
            f.write(str(key)+", "+', '.join(db[key])+'\n')
    del db
    return

def gdbm_open(filePath, mode):
    return open(filePath, mode, encoding='utf-8')

def gdbm_fetch(dbf, key):
    dbf.seek(0)
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    return db[key]

def gdbm_exists(dbf, key):
    dbf.seek(0)
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    if key in db: 
        del db
        return True
    else:
        del db
        return False
    
def gdbm_firstKey(dbf):
    dbf.seek(0)
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    key = next(iter(db))
    return key
    
def gdbm_nextKey(dbf, key):
    dbf.seek(0)
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    keys = list(db.keys())
    idx = keys.index(key)
    
    if idx+1 < len(keys): return keys[idx+1]
    else: return None

if __name__ == "__main__":
    path = '/'.join(os.path.abspath(__file__).split("\\")[:-1])+'/'
    dbf = gdbm_open(path+'tableA.csv', "r")
    gdbm_store(dbf, '0', '0', GDBM_REPLACE)