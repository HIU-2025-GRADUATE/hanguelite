class SelectQueryDTO:
    def __init__(self):
        self.flag = False
        self.columnNames:list[str] = []
        self.rows:list[tuple] = []
        self.logs:list[str] = []

    def setColumnNames(self, columnNames:list):
        self.columnNames = columnNames.copy()

    def addRow(self, row:list):
        self.rows.append(tuple(row))

    def addDebug(self, line:str):
        self.logs.append(line)

    def setFlag(self, val:bool):
        self.flag = val

    def getFlag(self):
        return self.flag
    
    def clearDto(self):
        self.flag = False
        self.columnNames.clear()
        self.rows.clear()
        self.logs.clear()

dto = SelectQueryDTO()