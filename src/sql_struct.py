"""
    The number of entries in the in-memory hash array holding the database schema.
"""
N_HASH = 51

"""
    Name of the master database table.
    The master database table is a special table
    that holds the names and attributes of all user tables and indices.
"""
MASTER_NAME = "hqlite_master"

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