class SelectQueryDTO:
    def __init__(self):
        self.flag = False
        self.columnNames:list[str] = []
        self.rows:list[tuple] = []

    def setColumnNames(self, columnNames:list):
        self.columnNames = columnNames.copy()

    def addRow(self, row:list):
        self.rows.append(tuple(row))


dto = SelectQueryDTO()