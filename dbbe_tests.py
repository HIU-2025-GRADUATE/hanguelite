from src.dbbe import *

class DbbeTest:
    def __init__(self, path):
        self.dbbe = Dbbe(path, True)
        self.dbbeCursor = DbbeCursor()

    def __del__(self):
        del self.dbbe
        del self.dbbeCursor

    # DbbeCursor -> openCursor
    def createNewDB(self, dbName):
        self.dbbeCursor.openCursor(self.dbbe, dbName, 'c')

    # DbbeCursor -> new, put
    def insertData(self):
        dt1 = ['권 찬', '26', '1']
        dt2 = ['김 태연', '26', '2']
        dt3 = ['유 호윤', '26', '3']
        dtList = [dt1, dt2, dt3]

        for dt in dtList:
            key = self.dbbeCursor.new()
            self.dbbeCursor.put(key, dt)

    # DbbeCursor -> nextKey, readData, readKey, rewind, fetch
    def readData(self):
        print("### readData ###")
        for _ in range(6):
            self.dbbeCursor.nextKey()
            l = ''
            for i in range(3):
                l += self.dbbeCursor.readData(i) + ' '
            print(self.dbbeCursor.readKey(), l)
        
        self.dbbeCursor.rewind()
        for _ in range(2):
            self.dbbeCursor.nextKey()
            key = self.dbbeCursor.readKey()
            print(key, self.dbbeCursor.fetch(key))

    # DbbeCursor -> delete
    def modifyData(self):
        key = self.dbbeCursor.readKey()
        self.dbbeCursor.delete(key)
        self.dbbeCursor.rewind()

    # Dbbe -> closeTempFile, openTempFile
    def testTempFile(self):
        apList = []
        apList.append(0)
        apList.append(0)
        self.dbbe.closeTempFile(apList, 1)
        self.dbbe.openTempFile(apList, 1)
        print(apList)
        self.dbbe.closeTempFile(apList, 1)
        print(apList)

    # Dbbe -> dropTable, fileOfTable
    # DbbeCursor -> closeCursor()
    def closeCursor(self):
        self.dbbeCursor.closeCursor()
        self.dbbe.dropTable(dbName)

if __name__ == '__main__':
    dbPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),'db')
    dbName = 'testTable'
    DT = DbbeTest(dbPath)
    DT.createNewDB(dbName)
    DT.insertData()
    DT.readData()
    DT.modifyData()
    DT.readData()
    DT.closeCursor()
    DT.testTempFile()