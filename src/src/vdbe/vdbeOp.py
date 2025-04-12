"""
** These are the available opcodes.
**
** If any of the values changes or if opcodes are added or removed,
** be sure to also update the zOpName[] array in sqliteVdbe.c to
** mirror the change.
**
** The source tree contains an AWK script named renumberOps.awk that
** can be used to renumber these opcodes when new opcodes are inserted.
"""
OP_Open          =      1
OP_Close         =      2
OP_Fetch         =      3
OP_Fcnt          =      4
OP_New           =      5
OP_Put           =      6
OP_Distinct      =      7
OP_Found         =      8
OP_NotFound      =      9
OP_Delete        =     10
OP_Field         =     11
OP_KeyAsData     =     12
OP_Key           =     13
OP_Rewind        =     14
OP_Next          =     15
OP_Destroy       =     16
OP_Reorganize    =     17

OP_ResetIdx      =     18
OP_NextIdx       =     19
OP_PutIdx        =     20
OP_DeleteIdx     =     21

OP_MemLoad       =     22
OP_MemStore      =     23
OP_ListOpen      =     24
OP_ListWrite     =     25
OP_ListRewind    =     26
OP_ListRead      =     27
OP_ListClose     =     28

OP_SortOpen      =     29
OP_SortPut       =     30
OP_SortMakeRec   =     31
OP_SortMakeKey   =     32
OP_Sort          =     33
OP_SortNext      =     34
OP_SortKey       =     35
OP_SortCallback  =     36
OP_SortClose     =     37

OP_FileOpen      =     38
OP_FileRead      =     39
OP_FileField     =     40
OP_FileClose     =     41

OP_AggReset      =     42
OP_AggFocus      =     43
OP_AggIncr       =     44
OP_AggNext       =     45
OP_AggSet        =     46
OP_AggGet        =     47

OP_SetInsert     =     48
OP_SetFound      =     49
OP_SetNotFound   =     50
OP_SetClear      =     51

OP_MakeRecord    =     52
OP_MakeKey       =     53

OP_Goto          =     54
OP_If            =     55
OP_Halt          =     56

OP_ColumnCount   =     57
OP_ColumnName    =     58
OP_Callback      =     59

OP_Integer       =     60
OP_String        =     61
OP_Null          =     62
OP_Pop           =     63
OP_Dup           =     64
OP_Pull          =     65

OP_Add           =     66
OP_AddImm        =     67
OP_Subtract      =     68
OP_Multiply      =     69
OP_Divide        =     70
OP_Min           =     71
OP_Max           =     72
OP_Like          =     73
OP_Glob          =     74
OP_Eq            =     75
OP_Ne            =     76
OP_Lt            =     77
OP_Le            =     78
OP_Gt            =     79
OP_Ge            =     80
OP_IsNull        =     81
OP_NotNull       =     82
OP_Negative      =     83
OP_And           =     84
OP_Or            =     85
OP_Not           =     86
OP_Concat        =     87
OP_Noop          =     88

OP_MAX           =     88

"""
** SQL is translated into a sequence of instructions to be
** executed by a virtual machine.  Each instruction is an instance
** of the following structure.
"""
class VdbeOp:
    pass