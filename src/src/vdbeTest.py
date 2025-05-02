from vdbe import *
from vdbeOp import *

if __name__ == "__main__":
    p = Vdbe()
    p.addOp(OP_Open, 1, 0, "tableA")
    p.addOp(OP_Close, 2)
    p.exec()
    print("MAIN")
    for row in csv.reader(p.pBe.pOpen.dbf):
        print(row)