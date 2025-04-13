from ..dbbe import DbbeCursor

"""
** A cursor is a pointer into a database file.  The database file
** can represent either an SQL table or an SQL index.  Each file is
** a bag of key/data pairs.  The cursor can loop over all key/data
** pairs (in an arbitrary order) or it can retrieve a particular
** key/data pair given a copy of the key.
**
** Every cursor that the virtual machine has open is represented by an
** instance of the following structure.
"""
class Cursor:
    pCursor: DbbeCursor  # /* The cursor structure of the backend */
    index: int           # /* The next index to extract */
    keyAsData: int       # /* The OP_Field command works on key instead of data */