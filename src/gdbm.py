import csv, os

GDBM_REPLACE = 0
GDBM_INSERT = 1

def gdbm_store(dbf=0, key='', data='', mode=0):
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    if mode == GDBM_INSERT and key in db.keys():
        return "ERROR"
    db[key]=data
    with open(os.path.abspath(dbf.name), "w", encoding='utf-8') as f:
        for key in db:
            f.write(str(key)+", "+', '.join(db[key])+'\n')
    del db
    return

def gdbm_open(filePath, mode):
    return open(filePath, mode, encoding='utf-8')

def gdbm_fetch():
    return

def gdbm_exists(dbf, key):
    db = {l[0]:l[1:] for l in csv.reader(dbf)}
    print(db.keys())
    if key in db.keys(): 
        del db
        return True
    else:
        del db
        return False


if __name__ == "__main__":
    path = '/'.join(os.path.abspath(__file__).split("\\")[:-1])+'/'
    dbf = gdbm_open(path+'tableA.csv', "r")
    gdbm_store(dbf, '0', '0', GDBM_REPLACE)