class Parse:

    def __init__(self):
        self.error_msg = ""
        self.error_count = 0
        self.new_table = None

    @staticmethod
    def empty():
        return Parse()

class Table:
    def __init__(self, name: str):
        self.name = name
        self.hash = 0
        self.column_count = 0
        self.columns = []
        self.index = None