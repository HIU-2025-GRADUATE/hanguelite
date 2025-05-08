"""
Name of the master database table.
The master database table is a special table that holds the names and attributes of all user tables and indices.
"""
MASTER_NAME = "hqlite_master"

SQLITE_OK        = 0    # /* Successful result */
SQLITE_INTERNAL  = 1    # /* An internal logic error in SQLite */
SQLITE_ERROR     = 2    # /* SQL error or missing database */
SQLITE_PERM      = 3    # /* Access permission denied */
SQLITE_ABORT     = 4    # /* Callback routine requested an abort */
SQLITE_BUSY      = 5    # /* One or more database files are locked */
SQLITE_NOMEM     = 6    # /* A malloc() failed */
SQLITE_READONLY  = 7    # /* Attempt to write a readonly database */

"""
Possible values for the sqlite.flags.
"""
SQLITE_VdbeTrace   = 0x00000001
SQLITE_Initialized = 0x00000002