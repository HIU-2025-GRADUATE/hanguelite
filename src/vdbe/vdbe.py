from src.dbbe import *
from .vdbeOp import VdbeOp
from src.vdbe.vdbeOp import *
from src.vdbe.cursor import *

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
    self.aCsr = list()
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
    # FILE **apList;     # /* An open file for each list */
    # int nSort;         # /* Number of slots in apSort[] */
    # Sorter **apSort;   # /* An open sorter list */
    # FILE *pFile;       # /* At most one open file handler */
    # int nField;        # /* Number of file fields */
    # char **azField;    # /* Data for each file field */
    # char *zLine;       # /* A single line from the input file */
    # int nLineAlloc;    # /* Number of spaces allocated for zLine */
    # int nMem;          # /* Number of memory locations currently allocated */
    # Mem *aMem;         # /* The memory locations */
    # Agg agg;           # /* Aggregate information */
    # int nSet;          # /* Number of sets allocated */
    # Set *aSet;         # /* An array of sets */
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
    return 0

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
    if addr<0 or addr>self.nOp: return
    self.aOp[addr-1] = self.aOp[addr-1].replace('"','')

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
  def hardStringify(self, i: int) -> int:
    pass
  #define Stringify(P,I) ((P->aStack[I].flags & STK_Str)==0 ? hardStringify(P,I) : 0)
  # static int hardStringify(Vdbe *p, int i){
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

  # /*
  # ** Convert the given stack entity into a integer if it isn't one
  # ** already.
  # **
  # ** Any prior string or real representation is invalidated.
  # ** NULLs are converted into 0.
  # */
  # #define Integerify(P,I) \
  #     if(((P)->aStack[(I)].flags&STK_Int)==0){ hardIntegerify(P,I); }
  # static void hardIntegerify(Vdbe *p, int i){
  #   if( p->aStack[i].flags & STK_Real ){
  #     p->aStack[i].i = p->aStack[i].r;
  #     Release(p, i);
  #   }else if( p->aStack[i].flags & STK_Str ){
  #     p->aStack[i].i = atoi(p->zStack[i]);
  #     Release(p, i);
  #   }else{
  #     p->aStack[i].i = 0;
  #   }
  #   p->aStack[i].flags = STK_Int;
  # }

  # /*
  # ** Get a valid Real representation for the given stack element.
  # **
  # ** Any prior string or integer representation is retained.
  # ** NULLs are converted into 0.0.
  # */
  # #define Realify(P,I) if(((P)->aStack[(I)].flags&STK_Real)==0){ hardRealify(P,I); }
  # static void hardRealify(Vdbe *p, int i){
  #   if( p->aStack[i].flags & STK_Str ){
  #     p->aStack[i].r = atof(p->zStack[i]);
  #   }else if( p->aStack[i].flags & STK_Int ){
  #     p->aStack[i].r = p->aStack[i].i;
  #   }else{
  #     p->aStack[i].r = 0.0;
  #   }
  #   p->aStack[i].flags |= STK_Real;
  # }

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
  ** This routine will automatically close any cursors, list, and/or
  ** sorters that were left open.
  """
  def cleanUp(self):
    pass
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
    while pc < self.nOp:
      # pc가 가리키는 명령어 실행
      pOp = self.aOp[pc]
      #print(pOp.opcode, pOp.p1, pOp.p2, pOp.p3)
      #print(self.aStack)

      # 특정 위치로 이동
      if pOp.opcode == OP_Goto:
        pc = pOp.p2 - 1                   #7 => makeLabel 없어서 하드 코딩
      
      # 종료
      elif pOp.opcode == OP_Halt:
        pc = len(self.aOp)-1

      # P1 정수 값을 스택에 추가
      elif pOp.opcode == OP_Integer:
        self.aStack.append(pOp.p1)

      # P3 문자열 값을 스택에 추가
      elif pOp.opcode == OP_String:
        self.aStack.append(pOp.p3)

      # NULL 값을 스택에 추가
      # (TODO) 일단 None 값으로 추가하였음 원본은 STK_Null 값 사용
      elif pOp.opcode == OP_Null:
        self.aStack.append(None)

      # 스택의 top에서 p1 개의 원소를 삭제제
      elif pOp.opcode == OP_Pop:
        for _ in range(pOp.p1):
          del self.aStack[-1]

      # 스택 위에서 P1 번째 원소를 복제해서 스택의 top에 추가
      elif pOp.opcode == OP_Dup:
        self.aStack.append(self.aStack[-(pOp.p1+1)])

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

        args = []
        for _ in range(argc):
          args.append(self.aStack.pop())

        if xCallback != None:
          print(f"call callback with args: {args}")
          xCallback(argc, args, [])


      elif pOp.opcode == OP_Concat:
        pass

      elif pOp.opcode in [OP_Add, OP_Subtract,OP_Multiply, OP_Divide]:
        pass

      elif pOp.opcode == OP_Max:
        pass

      elif pOp.opcode == OP_Min:
        pass

      elif pOp.opcode == OP_AddImm:
        pass

      # 스택의 top에서 원소 두개를 꺼내서 비교 연산 -> true이면 Goto p2
      # NOS (comp) TOS
      elif pOp.opcode in [OP_Eq, OP_Ne, OP_Lt, OP_Le, OP_Gt, OP_Ge]:
        tos = self.aStack[-1]
        del self.aStack[-1]
        nos = self.aStack[-1]
        del self.aStack[-1]

        if pOp.opcode == OP_Eq: c = (nos==tos)
        elif pOp.opcode == OP_Ne: c = (nos!=tos)
        elif pOp.opcode == OP_Lt: c = (nos<tos)
        elif pOp.opcode == OP_Le: c = (nos<=tos)
        elif pOp.opcode == OP_Gt: c = (nos>tos)
        elif pOp.opcode == OP_Ge: c = (nos>=tos)

        if c: pc = pOp.p2-1

      elif pOp.opcode == OP_Like:
        pass

      elif pOp.opcode == OP_Glob:
        pass

      elif pOp.opcode in [OP_And, OP_Or]:
        pass

      elif pOp.opcode == OP_Negative:
        pass

      elif pOp.opcode == OP_Not:
        pass

      elif pOp.opcode == OP_Noop:
        pass

      elif pOp.opcode == OP_If:
        pass

      elif pOp.opcode == OP_IsNull:
        pass

      elif pOp.opcode == OP_NotNull:
        pass

      # 스택의 top에서 p1개의 원소를 꺼내 Record로 만듬
      # (TODO) 원래는 헤더 + 데이터 구조로 이루어져 있는데
      # 굳이 그렇게할 필요 없을 것 같아서 일단 리스트 하나로 묶어서 Record로 만듬듬
      elif pOp.opcode == OP_MakeRecord:
        nField = pOp.p1
        record = self.aStack[-nField:]
        del self.aStack[-nField:]
        self.aStack.append(record)

      # 스택에서 P1개의 항목을 하나의 키 문자열로 합침 (spilter = '\t')
      # P2가 0이면 원소를 삭제 (pop), 1이면 유지
      elif pOp.opcode == OP_MakeKey:
        # (TODO) 오류 출력 만들어야함
        if len(self.aStack) < pOp.p1: return "Error"
        tmp = ""
        idx = len(self.aStack)-pOp.p1
        for _ in range(pOp.p1):
          tmp += str(self.aStack[idx])
          if pOp.p2: 
            del self.aStack[idx]
        self.aStack.append(tmp)

      elif pOp.opcode == OP_Open:
        i = pOp.p1
        if i < 0: return
        # (TODO) 이미 동일한 id가 존재하면 커서 삭제
        # p.aCsr[i].pCursor에 새로운 커서를 할당
        for j in range(self.nCursor, i+1): self.aCsr.append(0)
        self.nCursor = i+1
        self.aCsr[i] = Cursor()
        self.aCsr[i].pCursor.openCursor(self.pBe, pOp.p3, pOp.p2)
        self.aCsr[i].index = 0
        self.aCsr[i].keyAsData = 0

      elif pOp.opcode == OP_Close:
        i = pOp.p1
        if i >= 0 and i < self.nCursor and self.aCsr[i].pCursor!=0:
          self.aCsr[i].pCursor.closeCursor()
          #self.aCsr[i].pCursor = 0

      elif pOp.opcode == OP_Fetch:
        pass

      elif pOp.opcode == OP_Fcnt:
        pass

      elif pOp.opcode in [OP_Distinct, OP_NotFound, OP_Found]:
        pass

      # p1번째 커서와 연관된 키를 생성 (이전에 사용된적 없는 정수값)
      # 생성 후, 스택에 push
      elif pOp.opcode == OP_New:
        if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: v=0
        else: v = self.aCsr[pOp.p1].pCursor.new()
        self.aStack.append(v)

      elif pOp.opcode == OP_Put:
        if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: continue
        data = self.aStack[-1]
        key = self.aStack[-2]
        self.aCsr[pOp.p1].pCursor.put(key, data)
        self.aStack = self.aStack[:-2]
        pass

      elif pOp.opcode == OP_Delete:
        pass

      elif pOp.opcode == OP_KeyAsData:
        pass

      # p1 커서의 dbf 에서 p2 번째 필드 값을 읽어옴
      elif pOp.opcode == OP_Field:
        if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: continue
        z = self.aCsr[pOp.p1].pCursor.readData(pOp.p2)
        self.aStack.append(z)

      elif pOp.opcode == OP_Key:
        pass

      elif pOp.opcode == OP_Rewind:
        if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: continue
        self.aCsr[pOp.p1].pCursor.rewind()

      # p1 커서의 dbf 에서 가리키고 있는 레코드의 다음 레코드를 가리키도록 이동
      elif pOp.opcode == OP_Next:
        if pOp.p1<0 or pOp.p1>=self.nCursor or self.aCsr[pOp.p1]==0: continue
        if self.aCsr[pOp.p1].pCursor.nextKey() == 0: pc = pOp.p2-1            #16 => makeLabel 없어서 하드 코딩
        else: self.nFetch+=1

      elif pOp.opcode == OP_ResetIdx:
        pass

      elif pOp.opcode == OP_NextIdx:
        pass

      elif pOp.opcode == OP_PutIdx:
        pass

      elif pOp.opcode == OP_DeleteIdx:
        pass

      elif pOp.opcode == OP_Destroy:
        pass

      elif pOp.opcode == OP_ListOpen:
        pass

      elif pOp.opcode == OP_ListWrite:
        pass

      elif pOp.opcode == OP_ListRewind:
        pass

      elif pOp.opcode == OP_ListRead:
        pass

      elif pOp.opcode == OP_ListClose:
        pass

      elif pOp.opcode == OP_SortOpen:
        pass

      elif pOp.opcode == OP_SortPut:
        pass

      elif pOp.opcode == OP_SortMakeRec:
        pass

      elif pOp.opcode == OP_SortMakeKey:
        pass

      elif pOp.opcode == OP_Sort:
        pass

      elif pOp.opcode == OP_SortNext:
        pass

      elif pOp.opcode == OP_SortKey:
        pass

      elif pOp.opcode == OP_SortCallback:
        pass

      elif pOp.opcode == OP_SortClose:
        pass

      elif pOp.opcode == OP_FileOpen:
        pass

      elif pOp.opcode == OP_FileClose:
        pass

      elif pOp.opcode == OP_FileRead:
        pass

      elif pOp.opcode == OP_FileField:
        pass

      elif pOp.opcode == OP_MemStore:
        pass

      elif pOp.opcode == OP_MemLoad:
        pass

      elif pOp.opcode == OP_AggReset:
        pass

      elif pOp.opcode == OP_AggFocus:
        pass

      elif pOp.opcode == OP_AggIncr:
        pass

      elif pOp.opcode == OP_AggSet:
        pass

      elif pOp.opcode == OP_AggGet:
        pass

      elif pOp.opcode == OP_AggNext:
        pass

      elif pOp.opcode == OP_SetClear:
        pass

      elif pOp.opcode == OP_SetInsert:
        pass

      elif pOp.opcode == OP_SetFound:
        pass

      elif pOp.opcode == OP_SetNotFound:
        pass

      pc+=1


"""
** A translation from opcode numbers to opcode names.  Used for testing
** and debugging only.
**
** If any of the numeric OP_ values for opcodes defined in sqliteVdbe.h
** change, be sure to change this array to match.  You can use the
** "opNames.awk" awk script which is part of the source tree to regenerate
** this array, then copy and paste it into this file, if you want.
"""
zOpName = [ 0,
  "Open",           "Close",          "Fetch",          "Fcnt",
  "New",            "Put",            "Distinct",       "Found",
  "NotFound",       "Delete",         "Field",          "KeyAsData",
  "Key",            "Rewind",         "Next",           "Destroy",
  "Reorganize",     "ResetIdx",       "NextIdx",        "PutIdx",
  "DeleteIdx",      "MemLoad",        "MemStore",       "ListOpen",
  "ListWrite",      "ListRewind",     "ListRead",       "ListClose",
  "SortOpen",       "SortPut",        "SortMakeRec",    "SortMakeKey",
  "Sort",           "SortNext",       "SortKey",        "SortCallback",
  "SortClose",      "FileOpen",       "FileRead",       "FileField",
  "FileClose",      "AggReset",       "AggFocus",       "AggIncr",
  "AggNext",        "AggSet",         "AggGet",         "SetInsert",
  "SetFound",       "SetNotFound",    "SetClear",       "MakeRecord",
  "MakeKey",        "Goto",           "If",             "Halt",
  "ColumnCount",    "ColumnName",     "Callback",       "Integer",
  "String",         "Null",           "Pop",            "Dup",
  "Pull",           "Add",            "AddImm",         "Subtract",
  "Multiply",       "Divide",         "Min",            "Max",
  "Like",           "Glob",           "Eq",             "Ne",
  "Lt",             "Le",             "Gt",             "Ge",
  "IsNull",         "NotNull",        "Negative",       "And",
  "Or",             "Not",            "Concat",         "Noop",
]

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

