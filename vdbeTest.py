from src.vdbe.vdbe import *
from src.dbbe import *

if __name__ == "__main__":
  vdbe = Vdbe(Dbbe())
  vdbe.addOp(OP_Open, 0, 1, "MASTER_NAME")
  vdbe.addOp(OP_New, 0, 0, 0)
  vdbe.addOp(OP_String, 0, 0, 'table')
  vdbe.addOp(OP_String, 0, 0, 'tableName1')
  vdbe.addOp(OP_String, 0, 0, 'tableName2')
  vdbe.addOp(OP_String, 0, 0, 'Whole_Create_SQL')
  vdbe.addOp(OP_MakeRecord, 4, 0, 0)
  vdbe.addOp(OP_Put, 0, 0, 0)
  vdbe.addOp(OP_Close, 0, 0, 0)
  print(vdbe.nOp)
  vdbe.exec()
  del vdbe

  vdbe = Vdbe(Dbbe())
  vdbe.addOp(OP_ColumnCount, 3, 0, 0)
  vdbe.addOp(OP_ColumnName, 0, 0 , "name")
  vdbe.addOp(OP_ColumnName, 0, 0 , "age")
  vdbe.addOp(OP_ColumnName, 0, 0 , "grade")
  vdbe.addOp(OP_Open, 0, 0, "Student")
  vdbe.addOp(OP_Next, 0, 11, 0)   # 여기가 5번
  vdbe.addOp(OP_Field, 0, 0, 0)
  vdbe.addOp(OP_Field, 0, 1, 0)
  vdbe.addOp(OP_Field, 0, 2, 0)
  vdbe.addOp(OP_Callback, 3, 0, 0)
  vdbe.addOp(OP_Goto, 0, 5, 0)
  vdbe.addOp(OP_Close, 0, 0, 0)   # 여기가 11번
  print(vdbe.nOp)
  vdbe.exec()