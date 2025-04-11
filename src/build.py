from src.sql_struct import Parse, Table

def sql_exec(parse: Parse):
    pass

"""
    Begin constructing a new table representation in memory.
    This is the first of several action routines that get called in response to a CREATE TABLE statement.
"""
def sql_start_table(parse: Parse, table_name:str):
    table: Table = find_table(table_name)
    if table:
        parse.error_msg = "table %s already exists" % table_name
        parse.error_count += 1
        return

    # TODO : 입력으로 주어진 이름으로부터 인덱스가 존재하는지도 검증
    parse.new_table = Table(table_name)


"""
    This routine is called to report the final ")" that terminates a CREATE TABLE statement.
    The table structure is added to the internal hash tables.  
    An entry for the table is made in the master table on disk, unless initFlag==1.
    When initFlag==1, it means we are reading the master table because we just connected to the database,
    so the entry for this table already exists in the master table.
    We do not want to create it again.
"""
def sql_end_table(parse: Parse):
    if parse.error_count != 0:
        return

    table:Table = parse.new_table

    # True to insert a meta records into the file
    addMeta = table != None and parse.db.table_count == 1

    # Add the table to the in -memory representation of the database
    if table: # explain 문법은 고려하지 않음
        h = sql_hash_no_case(table.name, 0) % N_HASH
        table.hash = parse.db.table_hash[h]
        parse.db.table_hash[h] = table
        parse.new_table = None
        parse.db.table_count += 1

    # If not initializing, then create the table on disk.
    if not parse.init_flag:
        add_table_operations = [
            (OP_Open, 0, 1, MASTER_NAME),
            (OP_New, 0, 0, 0),
            (OP_String, 0, 0, "table"),
            (OP_String, 0, 0, table.name), # / * 3 * /
            (OP_String, 0, 0, table.name), # / * 4 * /
            (OP_String, 0, 0, 0), # / * 5 * /
            (OP_MakeRecord, 4, 0, 0),
            (OP_Put, 0, 0, 0),
        ]

        v = parse.get_vdbe()
        if not v:
            return

        # n = (int)pEnd->z - (int)pParse->sFirstToken.z + 1;
        # base = sqliteVdbeAddOpList(v, ArraySize(addTable), addTable);
        # sqliteVdbeChangeP3(v, base + 5, pParse->sFirstToken.z, n); # 전체 sql 문 저장
        v.add_op_list(add_table_operations)

        add_version_operations = [
            (OP_New, 0, 0, 0),
            (OP_String, 0, 0, "meta"),
            (OP_String, 0, 0, ""),
            (OP_String, 0, 0, ""),
            (OP_String, 0, 0, "file format 2"),
            (OP_MakeRecord, 4, 0, 0),
            (OP_Put, 0, 0, 0),
        ]

        if addMeta:
            v.add_op_list(add_version_operations)

        v.add_op(OP_Close, 0, 0, 0, 0)


"""
    Add a new column to the table currently being constructed.
"""
def sql_add_column(parse: Parse, column_name:str):
    table = parse.new_table
    if not table:
        return
    table.columns.append(column_name)

def find_table(table_name:str):
    return None
