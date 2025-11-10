from src.dbbe import *
from src.vdbe.vdbeOp import *
from src.vdbe.cursor import *
from src.vdbe.agg import *
from src.vdbe.sorter import *
from ..constant import SQLITE_INTERNAL, SQLITE_OK
from ..exception.exception import BadInstruction
from src.util import *
from src.dto.selectQueryDTO import *

#  Allowed values for Stack.flags
STK_Null = 0x0001     # Value is NULL */
STK_Str = 0x0002      # Value is a string */
STK_Int = 0x0004      # Value is an integer */
STK_Real = 0x0008     # Value is a real number */
STK_Dyn = 0x0010      # Need to call sqliteFree() on zStack[*] */

class Vdbe:
  """
  ** 기존의 createVdbe 함수가 Dbbe 를 인자로 받아서 VDBE 구조체 기반으로 메모리 할당해서 객체 만들고 포인터를 리턴하는 방식이었음.
  ** 이 로직은 정확히 생성자가 하는 일과 일치해서 해당 함수는 제거하고 생성자로 대체함.
  """
  def __init__(self, pBe: Dbbe):
    # DB backend 객체
    # self.pBe = 0
    # (ForTest) 임시 Dbbe 객체를 생성하였음
    # 실제는 main 파일에서 sqliteDbbeOpen 함수 호출을 통해 db 객체에 할당해야함    
    self.pBe: Dbbe = pBe

    # 실행을 아래 파일에 기록
    self.trace = None
    # opcode가 저장된 리스트
    self.aOp = list()
    # self.aOp의 길이
    self.nOp = 0
    # 피연산자 스택
    self.aStack = list()
    # 문자열 스택
    self.zStack = list()
    # 열려있는 커서 리스트 (Cursor 객체 리스트)
    self.aCsr : list[Cursor] = list()
    # self.aCsr의 길이
    self.nCursor = 0
    # 각 컬럼의 이름 리스트
    self.azColName = list()
    # FILE *trace;          # /* Write an execution trace here, if not NULL */
    # int nOpAlloc;      # /* Number of slots allocated for aOp[] */
    # int nLabel;        # /* Number of labels used */
    # int nLabelAlloc;   # /* Number of slots allocated in aLabel[] */
    # int *aLabel;       # /* Space to hold the labels */
    self.aLabel = list()
    # int tos;           # /* Index of top of stack */
    # int nStackAlloc;   # /* Size of the stack */
    # char **zStack;     # /* Text or binary values of the stack */
    # char **azColName;  # /* Becomes the 4th parameter to callbacks */
    # int nList;         # /* Number of slots in apList[] */
    self.apList = list()     # /* An open file for each list */
    # int nSort;         # /* Number of slots in apSort[] */
    # Sorter **apSort;   # /* An open sorter list */
    self.apSort = list()
    # FILE *pFile;       # /* At most one open file handler */
    # int nField;        # /* Number of file fields */
    # char **azField;    # /* Data for each file field */
    # char *zLine;       # /* A single line from the input file */
    # int nLineAlloc;    # /* Number of spaces allocated for zLine */
    # int nMem;          # /* Number of memory locations currently allocated */
    # Mem *aMem;         # /* The memory locations */
    self.agg: Agg = Agg()# /* Aggregate information */
    # int nSet;          # /* Number of sets allocated */
    self.aSet:list[set] = list()         # /* An array of sets */
    # OP_Fetch 명령어 실행 횟수
    self.nFetch = 0

  # 로그 파일 (trace) Setter
  def Trace(self, trace):
    self.trace = trace

  # op, p1, p2, p3 를 입력받아 VDBE.aOp에 추가
  # int sqliteVdbeAddOp(Vdbe *p, int op, int p1, int p2, const char *p3, int lbl){
  def addOp(self, op: int, p1: int, p2: int, p3: str, lbl: int=0) -> int:
    # (TODO) lbl 활용 부분 구현해야함
    if p2<0 and (-1-p2)<len(self.aLabel) and self.aLabel[-1-p2]>=0:
      p2 = self.aLabel[-1-p2]

    self.aOp.append(VdbeOp(op, p1, p2, p3))

    if lbl<0 and (-lbl)<=len(self.aLabel):
      self.aLabel[-1-lbl] = self.nOp
      for j in range(self.nOp):
        if self.aOp[j].p2 == lbl:
          self.aOp[j].p2 = self.nOp

    self.nOp+=1
    return self.nOp - 1

  """
  ** Resolve label "x" to be the address of the next instruction to
  ** be inserted.
  """
  # void sqliteVdbeResolveLabel(Vdbe * p, int x)
  def resolveLabel(self, x: int):
    if x<0 and -x<=len(self.aLabel):
      self.aLabel[-1-x] = self.nOp
      for j in range(self.nOp):
        # Lable Goto가 -(미정)인 opcode 업데이트
        if self.aOp[j].p2 == x:
          self.aOp[j].p2 = self.nOp
          
  """
  ** Return the address of the next instruction to be inserted.
  """
  def currentAddr(self) -> int:
    return self.nOp

  """
  ** Add a whole list of operations to the operation stack.  Return the
  ** address of the first operation added.
  """
  # TODO : nOp 필요한지 검토 필요, 필요 없으면 삭제
  def addOpList(self, nOp: int, aOp: list[VdbeOp]) -> int:
    for OP in aOp: self.aOp.append(OP)
    self.nOp += len(aOp)
    return 0

  """
  ** If the P3 operand to the specified instruction appears
  ** to be a quoted string token, then this procedure removes
  ** the quotes.
  **
  ** The quoting operator can be either a grave ascent (ASCII 0x27)
  ** or a double quote character (ASCII 0x22).  Two quotes in a row
  ** resolve to be a single actual quote character within the string.
  """
  # 입력받은 addr번째 inst의 p3에서 Quotation Mark (")를 제거
  def dequoteP3(self, addr: int):
    if addr < 0 or addr >= self.nOp:
      return
    
    s = self.aOp[addr].p3
    if len(s) < 2 or s[0] not in ("'", '"') or s[-1] != s[0]:
        return
    
    self.aOp[addr].p3 = s[1:-1].replace(s[0]*2, s[0])

  """
  ** On the P3 argument of the given instruction, change all
  ** strings of whitespace characters into a single space and
  ** delete leading and trailing whitespace.
  
  파이썬으로는 문자열 조작 메서드 딸깍이면 돼서 없어도 될 것 같기도?
  """
  # void sqliteVdbeCompressSpace(Vdbe *p, int addr){
  #   char *z;
  #   int i, j;
  #   if( addr<0 || addr>=p->nOp ) return;
  #   z = p->aOp[addr].p3;
  #   i = j = 0;
  #   while( isspace(z[i]) ){ i++; }
  #   while( z[i] ){
  #     if( isspace(z[i]) ){
  #       z[j++] = ' ';
  #       while( isspace(z[++i]) ){}
  #     }else{
  #       z[j++] = z[i++];
  #     }
  #   }
  #   while( i>0 && isspace(z[i-1]) ){
  #     z[i-1] = 0;
  #     i--;
  #   }
  # }

  """
  ** Create a new symbolic label for an instruction that has yet to be
  ** coded.  The symbolic label is really just a negative number.  The
  ** label can be used as the P2 value of an operation.  Later, when
  ** the label is resolved to a specific address, the VDBE will scan
  ** through its operation list and change all values of P2 which match
  ** the label into the resolved address.
  **
  ** The VDBE knows that a P2 value is a label because labels are
  ** always negative and P2 values are suppose to be non-negative.
  ** Hence, a negative P2 value is a label that has yet to be resolved.
  """
  # int sqliteVdbeMakeLabel(Vdbe *p)
  def makeLabel(self) -> int:
    # if len(self.aLabel)==0:
    #   return 0
    self.aLabel.append(-1)
    return -len(self.aLabel)

  """
  ** Convert the given stack entity into a string if it isn't one
  ** already.  Return non-zero if we run out of memory.
  **
  ** NULLs are converted into an empty string.
  """
  def hardStringifyAt(self, i: int):
    if self.aStack[i] is None:
      self.aStack[i] = ""
    else:
      self.aStack[i] = str(self.aStack[i])

  #define Stringify(P,I) ((P->aStack[I].flags & STK_Str)==0 ? hardStringifyAt(P,I) : 0)
  # static int hardStringifyAt(Vdbe *p, int i){
  #   char zBuf[30];
  #   int fg = p->aStack[i].flags;
  #   if( fg & STK_Real ){
  #     sprintf(zBuf,"%g",p->aStack[i].r);
  #   }else if( fg & STK_Int ){
  #     sprintf(zBuf,"%d",p->aStack[i].i);
  #   }else{
  #     p->zStack[i] = "";
  #     p->aStack[i].n = 1;
  #     p->aStack[i].flags |= STK_Str;
  #     return 0;
  #   }
  #   p->zStack[i] = sqliteStrDup(zBuf);
  #   if( p->zStack[i]==0 ) return 1;
  #   p->aStack[i].n = strlen(p->zStack[i])+1;
  #   p->aStack[i].flags |= STK_Str|STK_Dyn;
  #   return 0;
  # }

  """
  ** Release the memory associated with the given stack level
  """
  # #define Release(P,I)  if((P)->aStack[I].flags&STK_Dyn){ hardRelease(P,I); }
  # static void hardRelease(Vdbe *p, int i){
  #   sqliteFree(p->zStack[i]);
  #   p->zStack[i] = 0;
  #   p->aStack[i].flags &= ~(STK_Str|STK_Dyn);
  # }

  def hardIntegerifyAt(self, i : int):
    try:
      self.aStack[i] = int(self.aStack[i])
    except:
      self.aStack[i] = 0

  # /*
  # ** Get a valid Real representation for the given stack element.
  # **
  # ** Any prior string or integer representation is retained.
  # ** NULLs are converted into 0.0.
  # */
  def hardRealifyAt(self, i : int):
    try:
      self.aStack[i] = float(self.aStack[i])
    except:
      self.aStack[i] = 0.0

  # /*
  # ** Pop the stack N times.  Free any memory associated with the
  # ** popped stack elements.
  # */
  # static void PopStack(Vdbe *p, int N){
  #   if( p->zStack==0 ) return;
  #   while( p->tos>=0 && N-->0 ){
  #     int i = p->tos--;
  #     if( p->aStack[i].flags & STK_Dyn ){
  #       sqliteFree(p->zStack[i]);
  #     }
  #     p->aStack[i].flags = 0;
  #     p->zStack[i] = 0;
  #   }
  # }

  # /*
  # ** Make sure space has been allocated to hold at least N
  # ** stack elements.  Allocate additional stack space if
  # ** necessary.
  # **
  # ** Return 0 on success and non-zero if there are memory
  # ** allocation errors.
  # */
  # #define NeedStack(P,N) (((P)->nStackAlloc<=(N)) ? hardNeedStack(P,N) : 0)
  # static int hardNeedStack(Vdbe *p, int N){
  #   int oldAlloc;
  #   int i;
  #   if( N>=p->nStackAlloc ){
  #     oldAlloc = p->nStackAlloc;
  #     p->nStackAlloc = N + 20;
  #     p->aStack = sqliteRealloc(p->aStack, p->nStackAlloc*sizeof(p->aStack[0]));
  #     p->zStack = sqliteRealloc(p->zStack, p->nStackAlloc*sizeof(char*));
  #     if( p->aStack==0 || p->zStack==0 ){
  #       sqliteFree(p->aStack);
  #       sqliteFree(p->zStack);
  #       p->aStack = 0;
  #       p->zStack = 0;
  #       p->nStackAlloc = 0;
  #       return 1;
  #     }
  #     for(i=oldAlloc; i<p->nStackAlloc; i++){
  #       p->zStack[i] = 0;
  #       p->aStack[i].flags = 0;
  #     }
  #   }
  #   return 0;
  # }

  """
  ** Clean up the VM after execution.
  **
  ** This routine will automatically close any cursors, list, and/or sorters that were left open.
  """
  def cleanUp(self):
    for i in range(self.nCursor):
      self.aCsr[i].pCursor.closeCursor()
  # static void Cleanup(Vdbe *p){
  #   int i;
  #   PopStack(p, p->tos+1);
  #   sqliteFree(p->azColName);
  #   p->azColName = 0;
  #   for(i=0; i<p->nCursor; i++){
  #     if( p->aCsr[i].pCursor ){
  #       sqliteDbbeCloseCursor(p->aCsr[i].pCursor);
  #       p->aCsr[i].pCursor = 0;
  #     }
  #   }
  #   sqliteFree(p->aCsr);
  #   p->aCsr = 0;
  #   p->nCursor = 0;
  #   for(i=0; i<p->nMem; i++){
  #     if( p->aMem[i].s.flags & STK_Dyn ){
  #       sqliteFree(p->aMem[i].z);
  #     }
  #   }
  #   sqliteFree(p->aMem);
  #   p->aMem = 0;
  #   p->nMem = 0;
  #   for(i=0; i<p->nList; i++){
  #     if( p->apList[i] ){
  #       sqliteDbbeCloseTempFile(p->pBe, p->apList[i]);
  #       p->apList[i] = 0;
  #     }
  #   }
  #   sqliteFree(p->apList);
  #   p->apList = 0;
  #   p->nList = 0;
  #   for(i=0; i<p->nSort; i++){
  #     Sorter *pSorter;
  #     while( (pSorter = p->apSort[i])!=0 ){
  #       p->apSort[i] = pSorter->pNext;
  #       sqliteFree(pSorter->zKey);
  #       sqliteFree(pSorter->pData);
  #       sqliteFree(pSorter);
  #     }
  #   }
  #   sqliteFree(p->apSort);
  #   p->apSort = 0;
  #   p->nSort = 0;
  #   if( p->pFile ){
  #     if( p->pFile!=stdin ) fclose(p->pFile);
  #     p->pFile = 0;
  #   }
  #   if( p->azField ){
  #     sqliteFree(p->azField);
  #     p->azField = 0;
  #   }
  #   p->nField = 0;
  #   if( p->zLine ){
  #     sqliteFree(p->zLine);
  #     p->zLine = 0;
  #   }
  #   p->nLineAlloc = 0;
  #   AggReset(&p->agg);
  #   for(i=0; i<p->nSet; i++){
  #     SetClear(&p->aSet[i]);
  #   }
  #   sqliteFree(p->aSet);
  #   p->aSet = 0;
  #   p->nSet = 0;
  # }

  """
  ** Delete an entire VDBE.
  """
  # VDBE 인스턴스를 통째로 삭제
  def delete(self):
    del self

  """
  /*
  ** Execute the program in the VDBE.
  **
  ** If an error occurs, an error message is written to memory obtained
  ** from sqliteMalloc() and *pzErrMsg is made to point to that memory.
  ** The return parameter is the number of errors.
  **
  ** If the callback every returns non-zero, then the program exits
  ** immediately.  No error message but the function does return SQLITE_ABORT.
  **
  ** A memory allocation error causes this routine to return SQLITE_NOMEM
  ** and abandon furture processing.
  **
  ** Other fatal errors return SQLITE_ERROR.
  **
  ** If a database file could not be opened because it is locked by
  ** another database instance, then the xBusy() callback is invoked
  ** with pBusyArg as its first argument, the name of the table as the
  ** second argument, and the number of times the open has been attempted
  ** as the third argument.  The xBusy() callback will typically wait
  ** for the database file to be openable, then return.  If xBusy()
  ** returns non-zero, another attempt is made to open the file.  If
  ** xBusy() returns zero, or if xBusy is NULL, then execution halts
  ** and this routine returns SQLITE_BUSY.
  */
  """
  def exec(self, xCallback: callable=None, pArg=0, pzErrMsg: str=0, pBusyArg=0, xBusy=0) -> int:
    # program counter
    pc = 0
    rc = None

    print("-----")
    for _op in self.aOp:
      print(_op)
    print("-----")
    try:
      showHeader = True
      while pc < self.nOp:
        # pc가 가리키는 명령어 실행
        pOp = self.aOp[pc]
        # print(zOpName[pOp.opcode], pOp.p1, pOp.p2, pOp.p3)
        # print(self.aStack)

        if pOp.opcode == OP_Goto:
          pc = pOp.p2 - 1

        elif pOp.opcode == OP_Halt:
          pc = len(self.aOp)-1

        elif pOp.opcode == OP_Integer:
          self.aStack.append(pOp.p1)

        elif pOp.opcode == OP_String:
          self.aStack.append(pOp.p3)

        # NULL 값을 스택에 추가
        # (TODO) 일단 None 값으로 추가하였음 원본은 STK_Null 값 사용
        elif pOp.opcode == OP_Null:
          self.aStack.append(None)

        # 스택의 top에서 p1 개의 원소를 삭제제
        elif pOp.opcode == OP_Pop:
          for _ in range(pOp.p1):
            self.aStack.pop()

        # 스택 위에서 P1 번째 원소를 복제해서 스택의 top에 추가
        elif pOp.opcode == OP_Dup:
          self.aStack.append(self.aStack[-(pOp.p1 + 1)])

        # 스택 위에서 P1 번째 스택을 빼서 top에 추가
        # Pull 0 0 0 는 no-op
        elif pOp.opcode == OP_Pull:
          self.aStack.append(self.aStack[-(pOp.p1+1)])
          del self.aStack[-(pOp.p1+2)]

        # self.azColName 리스트의 길이 설정
        elif pOp.opcode == OP_ColumnCount:
          self.azColName = [0] * pOp.p1

        # azColName[p1]=p3 로 설정
        elif pOp.opcode == OP_ColumnName:
          self.azColName[pOp.p1] = pOp.p3

        elif pOp.opcode == OP_Callback:
          argc = pOp.p1
          if len(self.aStack) < argc:
            raise Exception("[OP_Callback] not enough stack")

          if tableName != 'hqlite_master' and not dto.getFlag():
            dto.setFlag(True)
            dto.setColumnNames(self.azColName)

          args = []
          for _ in range(argc):
            args.append(self.aStack.pop())

          args.reverse()
          
          if xCallback != None:
            print(f"call callback with args: {args}")
            xCallback(argc, args, [])
          else:
            print("### NEW ROW ADDED ###")
            dto.addRow(args)

        elif pOp.opcode == OP_Concat:
          nField = pOp.p1
          zSep = pOp.p3
          res = ''
          for _ in range(nField):
            res += self.aStack[-1]
            del self.aStack[-1]
            if not zSep == 0:
              res += zSep
          self.aStack.append(res)

        # 스택의 탑 원소를 a, 그 다음 원소를 b라고 했을 때
        # a와 b를 pop한 후에 b 값에 a 값을 연산한 결과를 push
        # Subtract 인 경우 b-a 값을 저장
        elif pOp.opcode in [OP_Add, OP_Subtract, OP_Multiply, OP_Divide]:
          a = self.aStack[-1]
          b = self.aStack[-2]
          flag = isinstance(a, int) and isinstance(b, int)

          if not flag:
            try:
              a = int(a)
              b = int(b)
            except:
              self.hardRealifyAt(len(self.aStack) - 1)
              self.hardRealifyAt(len(self.aStack) - 2)
              a = self.aStack[-1]
              b = self.aStack[-2]

          if pOp.opcode == OP_Add:
            b += a
          elif pOp.opcode == OP_Subtract:
            b -= a
          elif pOp.opcode == OP_Multiply:
            b *= a
          elif pOp.opcode == OP_Divide:
            if a == 0:
              b = None
            else:
              b /= a

          self.aStack.pop()
          self.aStack.pop()
          self.aStack.append(b)

        # 스택의 탑에서 원소 두 개를 꺼내 그중 큰 것을 push
        elif pOp.opcode == OP_Max:
          if len(self.aStack) < 2:
            raise RuntimeError("Not Enough Stack Element")

          tos = self.aStack[-1]
          nos = self.aStack[-2]
          copy = False

          if nos is None:
            copy = True

          elif isinstance(tos, int) and isinstance(nos, int):
            copy = nos < tos

          elif isinstance(tos, (int, float)) and isinstance(nos, (int, float)):
            copy = float(tos) > float(nos)

          else:
            self.hardStringifyAt(len(self.aStack) - 1)
            self.hardStringifyAt(len(self.aStack) - 2)
            copy = compare(self.aStack[-1], self.aStack[-2]) > 0

          if copy:
            self.aStack[-2] = self.aStack[-1]

          self.aStack.pop()

        # 스택의 탑에서 원소 두 개를 꺼내 그중 작은 것을 push
        elif pOp.opcode == OP_Min:
          if len(self.aStack) < 2:
            raise RuntimeError("Not Enough Stack Element")

          tos = self.aStack[-1]
          nos = self.aStack[-2]
          copy = False

          if nos is None:
            copy = True

          elif tos is None:
            copy = False

          elif isinstance(tos, int) and isinstance(nos, int):
            copy = nos > tos

          elif isinstance(tos, (int, float)) and isinstance(nos, (int, float)):
            copy = float(tos) < float(nos)

          else:
            self.hardStringifyAt(len(self.aStack) - 1)
            self.hardStringifyAt(len(self.aStack) - 2)
            copy = compare(self.aStack[-1], self.aStack[-2]) < 0

          if copy:
            self.aStack[-2] = self.aStack[-1]

          self.aStack.pop()

        # 스택의 top 원소에 p1을 더함
        elif pOp.opcode == OP_AddImm:
          self.hardIntegerifyAt(len(self.aStack) - 1)
          self.aStack[-1] += pOp.p1

        # 스택의 top에서 원소 두개를 꺼내서 비교 연산 -> true이면 Goto p2
        # NOS (comp) TOS
        elif pOp.opcode in [OP_Eq, OP_Ne, OP_Lt, OP_Le, OP_Gt, OP_Ge]:
          tos = self.aStack.pop()
          nos = self.aStack.pop()

          if pOp.opcode == OP_Eq: c = (nos==tos)
          elif pOp.opcode == OP_Ne: c = (nos!=tos)
          elif pOp.opcode == OP_Lt: c = (nos<tos)
          elif pOp.opcode == OP_Le: c = (nos<=tos)
          elif pOp.opcode == OP_Gt: c = (nos>tos)
          elif pOp.opcode == OP_Ge: c = (nos>=tos)

          if c: pc = pOp.p2-1

        elif pOp.opcode == OP_Like:
          if len(self.aStack) < 2:
            raise RuntimeError("Not Enough Stack Element")

          self.hardStringifyAt(len(self.aStack) - 1)
          self.hardStringifyAt(len(self.aStack) - 2)

          res = likeCompare(self.aStack[-1], self.aStack[-2])
          self.aStack.pop()
          self.aStack.pop()
          
          if pOp.p1:
            res = not res
          if res:
            pc = pOp.p2 - 1

        # 스택에서 tos는 글로브 패턴, nos는 패턴과 비교할 문자열
        # 비교 결과가 패턴과 일치하면 goto p2, 아니면 pass
        # 만약 p1!=0 이면 NOT GLOB로 동작, 두 값이 다르면 jump
        # * : 0개 이상 문자와 일치
        # ? : 단일 문자와 일치
        # [...] : 문자 범위 / [^...] : 범위 내에 없는 문자와 일치
        # 글로브 패턴은 대소문자를 구분함
        elif pOp.opcode == OP_Glob:
          tos = self.aStack.pop()
          nos = self.aStack.pop()
          c = globCompare(str(tos), str(nos))
          if pOp.p1:
            c = not c
          if c:
            pc = pOp.p2-1
          pass

        # 스택에서 원소 두개를 pop하여 두 원소로 논리 연산을 수행
        # 수행 결과를 스택에 push
        elif pOp.opcode in [OP_And, OP_Or]:
          tos = self.aStack.pop()
          nos = self.aStack.pop()

          if pOp.opcode == OP_And:
            self.aStack.append(tos and nos)
          else:
            self.aStack.append(tos or nos)

        # 스택의 top 원소를 숫자 값으로 간주하여 덧셈 역원을 push
        elif pOp.opcode == OP_Negative:
          tos = self.aStack.pop()
          self.aStack.append(-tos)

        # /* Opcode: Not * * *
        # **
        # ** Interpret the top of the stack as a boolean value.  Replace it
        # ** with its complement.
        # */
        # (TODO) 여기를 논리 구조상 Not으로 처리했는데 bitwise Not으로 바꿔야하나?
        elif pOp.opcode == OP_Not:
          self.hardIntegerifyAt(len(self.aStack) - 1)
          self.aStack[-1] = not self.aStack[-1]

        elif pOp.opcode == OP_Noop:
          pass

        elif pOp.opcode == OP_If:
          self.hardIntegerifyAt(len(self.aStack) - 1)
          c = self.aStack.pop()

          if c:
            pc = pOp.p2 - 1

        # (TODO) 일단 None 값으로 추가하였음 원본은 STK_Null 값 사용
        elif pOp.opcode == OP_IsNull:
          c = self.aStack.pop()
          if c is None:
            pc = pOp.p2 - 1

        # (TODO) 일단 None 값으로 추가하였음 원본은 STK_Null 값 사용
        elif pOp.opcode == OP_NotNull:
          c = self.aStack.pop()
          if c is not None:
            pc = pOp.p2 - 1

        # 스택의 top에서 p1개의 원소를 꺼내 Record로 만듬
        # (TODO) 원래는 헤더 + 데이터 구조로 이루어져 있는데
        # 굳이 그렇게할 필요 없을 것 같아서 일단 리스트 하나로 묶어서 Record로 만듬듬
        elif pOp.opcode == OP_MakeRecord:
          print("[MakeRecord]")
          nField = pOp.p1
          record = self.aStack[-nField:]
          del self.aStack[-nField:]
          self.aStack.append(record)

        # 스택에서 P1개의 항목을 하나의 키 문자열로 합침 (spilter = '\t')
        # P2가 0이면 원소를 삭제 (pop), 1이면 유지
        elif pOp.opcode == OP_MakeKey:
          # (TODO) 오류 출력 만들어야함
          nField = pOp.p1
          if len(self.aStack) < nField:
            raise RuntimeError("Not Enough Stack Element")

          start = len(self.aStack) - pOp.p1
          tmp = "\t".join([str(self.aStack[i]) if self.aStack[i] is not None else "" for i in range(start, len(self.aStack))])

          if pOp.p2 == 0:
            for _ in range(nField):
              self.aStack.pop()

          self.aStack.append(tmp)

        # Open P1 P2 P3
        #
        # P3 이름을 가진 파일의 새로운 커서를 연다.
        # 이 커서의 식별자는 음이 아닌 정수 P1 이고, 음수면 에러가 발생한다.
        # 만약 P1 식별자 위치에 다른 커서가 존재한다면, 이 커서를 먼저 닫는다.
        # VDBE 실행이 종료되면 모든 커서를 닫는다.
        #
        # P2 == 0 이면 readonly 모드이다.
        #
        # P3 가 null 또는 빈 문자열이면 임시파일을 만든다.
        # 임시파일은 커서가 닫힐 때 자동으로 삭제된다.
        elif pOp.opcode == OP_Open:
          i = pOp.p1
          writeable  = pOp.p2
          tableName = pOp.p3

          if i < 0:
            raise BadInstruction(f"illegal operation at {pc}")

          # P1 위치에 커서 생성, 이미 동일한 id가 존재하면 커서 삭제
          if i >= self.nCursor: # TODO : len(self.aCsr) 로 변경하고 nCursor 제거
            # p.aCsr[i].pCursor에 새로운 커서를 할당
            for j in range(self.nCursor, i+1):
              self.aCsr.append(0)
            self.nCursor = i+1
          elif self.aCsr[i].pCursor:
            self.aCsr[i].pCursor.closeCursor()

          # do-while 구현용 once 변수
          busy, once = False, True
          while busy or once:
            self.aCsr[i] = Cursor()
            # print(f"cursor open at {i} for table {tableName}")
            rc = self.aCsr[i].pCursor.openCursor(self.pBe, tableName, writeable)

            if rc == SQLITE_OK:
              busy = False
              break
            else:
              # TODO : 케이스 별로 구현
              pass

            if once:
              once = False

        elif pOp.opcode == OP_Close:
          i = pOp.p1
          if 0 <= i < self.nCursor and self.aCsr[i].pCursor != 0:
            # print(f"cursor closed at {i}")
            self.aCsr[i].pCursor.closeCursor()
            #self.aCsr[i].pCursor = 0

        # 스택의 top 에서 원소를 하나 꺼낸 후, 이 값을 key 로 하는 record를
        # p1 커서에서 읽어옴 (fetch)
        # p1 커서에 key/data 쌍은 미리 존재함으로 간주
        elif pOp.opcode == OP_Fetch:
          i = pOp.p1
          key = self.aStack.pop()
          if  0 <= i < self.nCursor and self.aCsr[i].pCursor is not None:
            self.aCsr[i].pCursor.fetch(key)
            self.nFetch += 1

        # 이 vdbe에서 실행된 OP_Fetch의 횟수를 스택에 push
        # SQLite만 알아듣는 inst로 만들어서 테스트를 목적으로 만들었음
        elif pOp.opcode == OP_Fcnt:
          self.aStack.append(self.nFetch)

        # p1 커서에 스택 top의 값을 키로 가지는 레코드가 존재하는지 검사
        # OP_Distinct : 존재하지 않으면 goto p2, 스택의 top을 pop하지 않음
        # OP_Found : 존재하면 goto p2, 스택의 top을 pop
        # OP_NotFound : 존재하지 않으면 goto p2, 스택의 top을 pop
        elif pOp.opcode in [OP_Distinct, OP_NotFound, OP_Found]:
          i = pOp.p1
          tos = self.aStack[-1]
          alreadyExists = 0
          if i >= 0 and i < self.nCursor and self.aCsr[i].pCursor!=0:
            alreadyExists = self.aCsr[i].pCursor.test(str(tos))

          if pOp.opcode == OP_Found:
            if alreadyExists:
              pc = pOp.p2 - 1
          else:
            if not alreadyExists:
              pc = pOp.p2 - 1

          if pOp.opcode != OP_Distinct:
            del self.aStack[-1]

        # p1번째 커서와 연관된 키를 생성 (이전에 사용된적 없는 정수값)
        # 생성 후, 스택에 push
        elif pOp.opcode == OP_New:
          if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: v=0
          else: v = self.aCsr[pOp.p1].pCursor.new()
          self.aStack.append(v)

        elif pOp.opcode == OP_Put:
          print("cursor id:", pOp.p1)
          if pOp.p1 < 0 or pOp.p1 >= self.nCursor or self.aCsr[pOp.p1] == 0:
            pc += 1
            continue
          data = self.aStack[-1]
          key = self.aStack[-2]
          self.aCsr[pOp.p1].pCursor.put(key, data)
          self.aStack = self.aStack[:-2]
          pass

        # 스택의 top을 key로 하는 레코드를 p1 번째 커서의 db 파일에서 삭제
        # 사용된 스택의 top은 pop
        elif pOp.opcode == OP_Delete:
          tos = self.aStack.pop()
          i = pOp.p1
          if i >= 0 and i < self.nCursor and self.aCsr[i].pCursor!=0:
            self.aCsr[i].pCursor.delete(tos)
          pass

        # p1 커서에 key-as-data 모드를 p2로 설정 (0=Off / 1=On)
        # key-as-data 모드에서 OP_Field 명령어는 데이터 대신 key를 가져옴
        elif pOp.opcode == OP_KeyAsData:
          i = pOp.p1
          if i >= 0 and i < self.nCursor and self.aCsr[i].pCursor!=0:
            self.aCsr[i].keyAsData = pOp.p2

        # p1 커서의 최근에 가져온 데이터에서 p2 번째 필드 값을 읽어옴
        # 만약 조회하는 커서의 KeyAsData 값이 1 이라면 데이터 대신 키 값을 읽어옴
        elif pOp.opcode == OP_Field:
          if pOp.p1 < 0 or pOp.p1 >= self.nCursor or self.aCsr[pOp.p1].pCursor == 0:
            pc += 1
            continue
          if self.aCsr[pOp.p1].keyAsData:
            z = self.aCsr[pOp.p1].pCursor.readKey()
          else:
            z = self.aCsr[pOp.p1].pCursor.readData(pOp.p2)
          self.aStack.append(z)

        # 최근 사용한 키를 가져온다.
        # 원본에서는 cursor 의 keyAsData 속성에 따라 일부만 가져오거나 전체를 가져올 수 있다.
        # 파이썬은 자료형 크기의 제한이 없으므로 일단 전체 키를 가져오는 것을 기본으로 한다.
        elif pOp.opcode == OP_Key:
          i = pOp.p1
          if 0 <= i < self.nCursor and self.aCsr[i].pCursor is not None:
            z = self.aCsr[i].pCursor.readKey() # byte 형식의 키를 읽어온다.
            self.aStack.append(z)

        elif pOp.opcode == OP_Rewind:
          if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: 
            pc += 1
            continue
          self.aCsr[pOp.p1].pCursor.rewind()

        # p1 커서의 dbf 에서 가리키고 있는 레코드의 다음 레코드를 가리키도록 이동
        elif pOp.opcode == OP_Next:
          if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: 
            pc += 1
            continue
          if self.aCsr[pOp.p1].pCursor.nextKey() == 0: pc = pOp.p2-1            #16 => makeLabel 없어서 하드 코딩
          else: self.nFetch+=1

        # p1 커서의 다음 커서를 처음 커서 (0번) 으로 리셋
        elif pOp.opcode == OP_ResetIdx:
          i = pOp.p1
          if 0 <= i < self.nCursor:
            self.aCsr[i].index = 0

        # ** P1 커서는 SQL 인덱스를 가리킵니다. 해당 커서로
        # ** 가장 최근에 가져온 데이터는 여러 개의 정수들로 이루어져 있으며,
        # ** 각 정수는 SQL 테이블 파일의 레코드 키입니다.
        # ** 이 명령은 P1의 데이터에서 다음 정수 테이블 키를 가져와
        # ** 스택에 푸시합니다. fetch 이후 이 명령이 처음 실행되면
        # ** 첫 번째 정수 테이블 키가 푸시되고, 이후 실행될 때마다
        # ** 다음 정수 테이블 키가 순차적으로 푸시됩니다.
        # **
        # ** 이 명령을 실행할 때 P1의 데이터에 더 이상 정수 테이블 키가
        # ** 남아 있지 않다면, 아무 것도 푸시하지 않고 즉시 P2에 해당하는
        # ** 명령으로 점프합니다.
        
        # TODO: 여기 로직 다 변경됐음. 확인 필요
        elif pOp.opcode == OP_NextIdx:
          i = pOp.p1
          pCrsr = self.aCsr[i].pCursor
          if i >= 0 and i < self.nCursor and pCrsr:
            k = pCrsr.dataLength()

            j = self.aCsr[i].index
            while j < k:
              if pCrsr.data[j] != 0:
                self.aStack.append(pCrsr.data[j])
                break
              j += 1
            
            if j >= k:
              j = -1
              pc = pOp.p2 - 1
            
            self.aCsr[i].index = j+1

        # 스택의 top은 SQL index 키, 그 다음 값은 SQL table entry 키인 정수 값
        # tos의 인덱스 키와 일치하는 레코드를 p1 커서에서 찾고 없다면 새 레코드를 생성
        # 그 후 해당 레코드의 데이터에 정수 테이블 키를 추가하고 p1 커서 파일에 작성
        
        # TODO: 여기 로직 다 변경됐음. 확인 필요
        elif pOp.opcode == OP_PutIdx:
          i = pOp.p1
          tos = self.aStack.pop()
          nos = self.aStack.pop()
          pCrsr = self.aCsr[i].pCursor

          if i >= 0 and i < self.nCursor and pCrsr != 0:
            # 원본 소스코드는 굉장히 복잡해 보이지만 메모리 관리 때문에 케이스가 나뉨
            # 파이썬에서는 메모리 관리를 신경쓰지 않기 때문에 간소화
            # HACK: pCrsr에 key=tos, value=nos로 가지는 행 put
            r = pCrsr.fetch(tos)

            if r == 0:
              pCrsr.put(tos, nos)

            else:
              pCrsr.data.append(nos)
              pCrsr.put(tos, pCrsr.data)
        
        # 스택의 top은 SQL index 키, 그 다음 값은 SQL table entry 키인 정수 값
        # p1 커서에서 tos에 있는 인덱스 키와 일치하는 레코드를 찾고
        # 해당 레코드에 포함된 정수 테이블 키 목록에서 nos 키 값과 일치하는 항목을 제거하고
        # 수정된 데이터를 동일한 키로 p1 파일에 다시 작성
        # 만약 해당 작업으로 p1 커서의 데이터에서 마지막 정수 테이블 키까지 모두 제거되면
        # p1 커서에서 대응되는 레코드도 삭제
        elif pOp.opcode == OP_DeleteIdx:
          i = pOp.p1
          tos = self.aStack.pop()
          nos = self.aStack.pop()
          pCrsr = self.aCsr[i].pCursor

          if i >= 0 and i < self.nCursor and pCrsr != 0:
            r = pCrsr.fetch(tos)

            if r == 0:
              pc += 1
              continue

            if len(pCrsr.data) == 1 and pCrsr.data[0] == nos:
              pCrsr.delete(tos)

            else:
              try:
                idx = pCrsr.data.index(nos)
              except:
                pc += 1
                continue
              del pCrsr.data[idx]
              pCrsr.put(tos, pCrsr.data)

        # 파일 이름이 p3 인 파일을 디스크에서 삭제
        elif pOp.opcode == OP_Destroy:
          self.pBe.dropTable(pOp.p3)

        # 정수 키를 저장할 temporary file 을 open
        # p1 값을 이후 interaction 에서 해당 파일에 접근하기 위한 인덱스로 사용
        # 이미 p1 인덱스에 파일이 열려있다면 닫고 새로운 파일을 생성
        elif pOp.opcode == OP_ListOpen:
          i = pOp.p1
          if i >= len(self.apList):
            for j in range(len(self.apList), i+1):
              self.apList.append(0)
          elif self.apList:
            self.pBe.closeTempFile(self.apList, i)
          
          rc = self.pBe.openTempFile(self.apList, i)

        # 스택의 top을 pop해서 p1 번째 임시 파일에 쓰기
        # (TODO) 원본 코드는 int 크기를 기준으로 데이터를 구분하지만 여기선 \n 으로 작성
        elif pOp.opcode == OP_ListWrite:
          i = pOp.p1
          if i < len(self.apList) and self.apList[i] != 0:
            val = self.aStack.pop()
            self.apList[i].write(str(val)+'\n')

        # p1 임시 파일 객체의 커서를 처음으로 되돌림
        elif pOp.opcode == OP_ListRewind:
          i = pOp.p1
          if i < len(self.apList) and self.apList[i] != 0:
            self.apList[i].seek(0)

        # p1 임시 파일에서 정수 값 하나를 읽어 스택에 push
        # 만약 파일이 비어있다면 아무 동작하지 않고 p2로 jump
        elif pOp.opcode == OP_ListRead:
          i = pOp.p1
          if i < 0 or i > len(self.apList) or self.apList[i] == 0:
            # (TODO) continue 아니고 bad_instruction 오류로 수정해야함
            raise BadInstruction(f"illegal operation at {pc}")

          val = self.apList[i].readline()
          if val == '':
            pc = pOp.p2-1
          else:
            import ast
            b = ast.literal_eval(val) # 문자열로 된 byte 형식 데이터를 파이썬 byte 객체로 변환
            self.aStack.append(b)

        # p1 번째 임시 파일을 닫고 내용을 삭제
        elif pOp.opcode == OP_ListClose:
          i = pOp.p1
          if i < len(self.apList) and self.apList[i] != 0:
            self.pBe.closeTempFile(self.apList, i)
            self.apList[i] = 0

        # p1 인덱스에 sorter 객체 생성
        elif pOp.opcode == OP_SortOpen:
          i = pOp.p1
          if i >= len(self.apSort):
            for j in range(len(self.apSort), i+1):
              self.apSort.append(0)

        # tos 값은 key, nos 값은 data 로 취급하여 둘 다 스택에서 pop
        # 그 후 sorter에 집어넣음
        elif pOp.opcode == OP_SortPut:
          i = pOp.p1
          key = str(self.aStack.pop())
          data = str(self.aStack.pop())
          if i < 0 or i >= len(self.apSort):
            # (TODO) continue 아니고 bad_instruction 오류 발생해야함
            raise BadInstruction(f"illegal operation at {pc}")
          
          pSorter = Sorter()
          pSorter.pNext = self.apSort[i]
          self.apSort[i] = pSorter
          pSorter.nKey = len(key)
          pSorter.zKey = key
          pSorter.nData = len(data)
          pSorter.pData = data

        # 스택의 top에서부터 p1개 원소는 callback 인자로 사용
        # 이 원소들을 하나의 레코드로 결합하여 Sorter에 저장 후 나중에 SortCallback에 전달
        elif pOp.opcode == OP_SortMakeRec:
          nField = pOp.p1
          azArg = list()
          for _ in range(nField):
            val = self.aStack.pop()
            azArg.insert(0, val)
          self.aStack.append(azArg)

        # 스택의 top부터 여러 개의 원소를 정렬 키(sort key)로 반환
        # 소비될 원소의 개수는 문자열 p3의 문자 수와 동일함
        # p3의 각 문자를 스택 원소에 하나씩 연결하는데
        # 첫 번째 문자는 가장 낮은 원소에, 마지막 문자는 스택의 최상단 원소에 붙음
        # 모든 스택 요소는 \000 문자로 구분되며, 연속된 \000 이 등장하면 종료
        elif pOp.opcode == OP_SortMakeKey:
          nField = len(pOp.p3)
          zNewKey = ''
          for i in range(nField):
            j = len(self.aStack) - nField + i
            zNewKey += str(pOp.p3[i]) + str(self.aStack[j])+'\000'

          for _ in range(nField):
            self.aStack.pop()
          
          self.aStack.append(zNewKey)

        # merge sort로 sorter에 있는 모든 원소를 정렬
        elif pOp.opcode == OP_Sort:
          j = pOp.p1
          # Number of buckets used for merge-sort.
          NSORT = 30
          if j <len(self.apSort):
            apSorter = [0] * NSORT

            while self.apSort[j] != 0:
              pElem = self.apSort[j]
              self.apSort[j] = pElem.pNext
              pElem.pNext = 0
              for i in range(NSORT-1):
                if apSorter[i] == 0:
                  apSorter[i] = pElem
                  break
                else:
                  pElem = Merge(apSorter[i], pElem)
                  apSorter[i] = 0

              if i >= NSORT-1:
                apSorter[NSORT-1] = Merge(apSorter[NSORT-1], pElem)
            
            pElem = 0
            for i in range(NSORT):
              pElem = Merge(apSorter[i], pElem)

            self.apSort[j] = pElem

        # p1 sorter의 topmost 원소의 데이터를 스택에 push 후, sorter에서 원소 삭제
        elif pOp.opcode == OP_SortNext:
          i = pOp.p1
          if i < 0:
            raise BadInstruction(f"illegal operation at {pc}")
          if i < len(self.apSort) and self.apSort[i] != 0:
            pSorter = self.apSort[i]
            self.apSort[i] = pSorter.pNext
            self.aStack.append(pSorter.pData)
            del pSorter
          else:
            pc = pOp.p2 - 1

        # p1 sorter의 topmost 원소의 key를 스택에 push
        # sorter는 건들지 않음
        elif pOp.opcode == OP_SortKey:
          i = pOp.p1
          if i < 0 or i >= len(self.apSort):
            pSorter = self.apSort[i]
            self.aStack.append(pSorter.zKey)

        # 스택의 top에는 SortMakeRec에 의해 생성된 callback record가 존재
        # 해당 값을 pop 해서 callback을 실행
        elif pOp.opcode == OP_SortCallback:
          import ast
          record = ast.literal_eval(self.aStack.pop())
          
          if tableName != 'hqlite_master' and not dto.getFlag():
            dto.setFlag(True)
            dto.setColumnNames(self.azColName)

          if xCallback != None:
            xCallback(pOp.p1, record, [])
          else:
            print("### NEW ROW ADDED ###")
            dto.addRow(record)

        # p1 sorter를 닫고 모든 원소를 삭제
        elif pOp.opcode == OP_SortClose:
          i = pOp.p1
          if i < len(self.apSort):
            pSorter = self.apSort[i]
            while pSorter != 0:
              self.apSort[i] = pSorter.pNext
              del pSorter
              pSorter - self.apSort[i]

        # 이름이 p3인 파일을 읽기 모드로 open
        # 만약 p3가 'stdin'이면 표준 입력을 받음
        elif pOp.opcode == OP_FileOpen:
          if self.pFile:
            if self.pFile != sys.stdin:
              self.pFile.close()
            self.pFile = 0

          if pOp.p3 == 'stdin':
            self.pFile = sys.stdin
          else:
            self.pFile = open(pOp.p3, 'r')

          if self.pFile == 0:
            rc = SQLITE_ERROR
            
        # FileOpen으로 열었던 파일을 닫습니다
        # 이전에 FileOpen을 하지 않았다면 no-op
        elif pOp.opcode == OP_FileClose:
          if self.pFile:
            if self.pFile != sys.stdin:
              self.pFile.close()
            self.pFile = 0

        # 열린 파일에서 한 줄의 입력을 받음, 만약 EOF에 도달했다면 p2로 jump
        # 새로운 줄을 읽으면 p3를 구분자로 사용
        # 입력 한 줄에 p1 개의 필드가 존재, 초과 시 무시되고 부족하면 빈 문자열로 간주
        # (TODO) 미완성... 로직이 너무 길고 복잡해
        elif pOp.opcode == OP_FileRead:
          if self.pFile == 0:
            # (TODO) goto fileread_jump;
            pc += 1
            continue

          nField = pOp.p1

          if nField != self.nField or self.azField == 0:
            if self.azField == 0:
              self.nField = 0
              # (TODO) goto fileread_jump;
              continue
            self.nField = nField

          
          pass

        # 가장 최근에 읽은 줄에서 p1 번째 필드를 스택에 push
        elif pOp.opcode == OP_FileField:
          i = pOp.p1
          if i >= 0 and i < self.nField and self.azField:
            z = self.azField[i]
          else:
            z = ''
          self.aStack.append(z)

        elif pOp.opcode == OP_MemStore:
          pass

        elif pOp.opcode == OP_MemLoad:
          pass

        elif pOp.opcode == OP_AggReset:
          self.agg.reset()
          self.agg.nMem = pOp.p2

        elif pOp.opcode == OP_AggFocus:
          zKey = str(self.aStack.pop())
          if self.agg.nHash <= 0:
            pElem = None
          else:
            h = hashNoCase(zKey, len(zKey)) % self.agg.nHash    #TODO GROUP BY 절에 다수의 COLUMN이 있는 경우에 대해 좀 더 보완해야 함
            pElem = self.agg.apHash[h]
            while pElem:
              if pElem.zKey == zKey:
                break
              pElem = pElem.pHash

          if pElem:
            self.agg.pCurrent = pElem
            pc = pOp.p2 - 1
          else:
            self.agg.insert(zKey)

        elif pOp.opcode == OP_AggIncr:   # 정확한 구현인지 확인 필요. Mem을 안 써서 원본 코드와 완벽히 일치 X
          pFocus = self.agg.aggInFocus()
          i = pOp.p2

          if 0 <= i < self.agg.nMem:
            try:
              val = int(pFocus.aMem[i])
            except:
              val = 0

            pFocus.aMem[i] = val + pOp.p1

        elif pOp.opcode == OP_AggSet:
          pFocus = self.agg.aggInFocus()
          if 0 <= pOp.p2 < self.agg.nMem:
            pFocus.aMem[pOp.p2] = self.aStack.pop()

        elif pOp.opcode == OP_AggGet:
          pFocus = self.agg.aggInFocus()
          if 0 <= pOp.p2 < self.agg.nMem:
            self.aStack.append(pFocus.aMem[pOp.p2])

        elif pOp.opcode == OP_AggNext:
          if self.agg.nHash:
            self.agg.nHash = 0
            self.agg.apHash = None
            self.agg.pCurrent = self.agg.pFirst

          elif self.agg.pCurrent == self.agg.pFirst and self.agg.pCurrent:
            pElem = self.agg.pCurrent
            self.agg.pCurrent = self.agg.pFirst = pElem.pNext
            self.agg.nElem -= 1

          if self.agg.pCurrent is None:
            pc = pOp.p2 - 1

        elif pOp.opcode == OP_SetClear:
          pass

        elif pOp.opcode == OP_SetInsert:
          i = pOp.p1
          if len(self.aSet) <= i:
            while len(self.aSet) <= i:
              self.aSet.append(None)
            self.aSet[i] = set()

          if pOp.p3:
            self.aSet[i].add(pOp.p3.lower())
          else:
            self.hardStringifyAt(len(self.aStack) - 1)
            self.aSet[i].add(self.aStack[-1].lower())
            self.aStack.pop()

        elif pOp.opcode == OP_SetFound:
          i = pOp.p1
          self.hardStringifyAt(len(self.aStack) - 1)

          if 0 <= i < len(self.aSet) and self.aStack[-1].lower() in self.aSet[i]:
            pc = pOp.p2 - 1

          self.aStack.pop()

        elif pOp.opcode == OP_SetNotFound:
          i = pOp.p1
          self.hardStringifyAt(len(self.aStack) - 1)

          if 0 <= i < len(self.aSet) and not self.aStack[-1].lower() in self.aSet[i]:
            pc = pOp.p2 - 1

          self.aStack.pop()

        pc+=1

      self.cleanUp()
      return rc
    except BadInstruction as e:
      rc = SQLITE_INTERNAL
      print(e)
      return rc
    except Exception as e:
      raise e

"""
** Given the name of an opcode, return its number.  Return 0 if
** there is no match.
**
** This routine is used for testing and debugging.
"""
def opcode(zName: str) -> int:
  pass
# int sqliteVdbeOpcode(const char *zName){
#   int i;
#   for(i=1; i<=OP_MAX; i++){
#     if( sqliteStrICmp(zName, zOpName[i])==0 ) return i;
#   }
#   return 0;
# }

def ADDR(x: int):
  return -1-x
