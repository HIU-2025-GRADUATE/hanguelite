N_CHAR_CLASS = 5 

_state_machine = [
    # State 0: Beginning of word
      1, 0, 2, 3, 1,
    # State 1: Arbitrary text
      1, 0, 2, 1, 1,
    # State 2: Integer
      1, 0, 2, 1, 4,
    # State 3: Negative integer
      1, 0, 3, 1, 5,
    # State 4: Real number
      1, 0, 4, 1, 1,
    # State 5: Negative real num
      1, 0, 5, 1, 1,
]

def hashNoCase(z : str, n : int):
    h = 0
    if n <= 0:
        n = len(z)

    for i in range(n):
        h = (h << 3) ^ h ^ ord(z[i].lower())

    if h < 0:
        h = -h
    return h

def likeCompare(pattern : str, target : str):
    i = j = 0
    while i < len(pattern):
        c = pattern[i].lower()
        if c == '%':
            while i + 1 < len(pattern) and pattern[i + 1] == '%':
                i += 1
            if i + 1 == len(pattern):
                return 1  
            next = pattern[i + 1].lower()
            if next == '_':
                while j < len(target):
                    if likeCompare(pattern[i + 1:], target[j:]):
                        return 1
                    j += 1
                return 0
            else:
                while j < len(target):
                    if target[j].lower() == next:
                        if likeCompare(pattern[i + 1:], target[j:]):
                            return 1
                    j += 1
                return 0
        elif c == '_':
            if j >= len(target):
                return 0
        else:
            if j >= len(target) or c != target[j].lower:
                return 0
        i += 1
        j += 1

    return j == len(target)

# int sqliteGlobCompare(const char *zPattern, const char *zString)
def globCompare(pattern : str, target : str):
    i = 0
    j = 0

    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            while i + 1 < len(pattern) and pattern[i + 1] == '*':
                i += 1
            if i + 1 == len(pattern):
                return 1
            c = pattern[i + 1]
            if c in ['[', '?']:
                while j < len(target) and not globCompare(pattern[i + 1:], target[j:]):
                    j += 1
                return 1 if j < len(target) else 0
            else:
                while j < len(target):
                    while j < len(target) and target[j] != c:
                        j += 1
                    if j == len(target):
                        return 0
                    if globCompare(pattern[i + 1:], target[j:]):
                        return 1
                    j += 1
                return 0
        elif c == '?':
            if j == len(target):
                return 0
        elif c == '[':
            seen = False
            invert = False
            if j == len(target):
                return 0
            c = target[j]
            i += 1
            c2 = pattern[i]
            if c2 == '^':
                invert = True
                i += 1
                c2 = pattern[i]
            if c2 == ']':
                if c == ']':
                    seen = True
                i += 1
                c2 = pattern[i]
            while i < len(pattern) and c2 != ']':
                if c2 == '-' and i + 1 < len(pattern) and pattern[i + 1] != ']':
                    if ord(pattern[i - 1]) < ord(c) < ord(pattern[i + 1]):
                        seen = True
                elif c == c2:
                    seen = True
                i += 1
                if i < len(pattern):
                    c2 = pattern[i]
            if c2 == 0 or (seen ^ invert) == 0:
                return 0
        else:
            if c != target[j]:
                return 0
        i += 1
        j += 1

    return int(j == len(target))

def _char_class(ch: str):
    if ch == '\0':
        return 1  
    if ch.isspace():
        return 1
    if ch.isdigit():
        return 2
    if ch == '-':
        return 3
    if ch == '.':
        return 4
    return 0

def _private_str_cmp(a_text: str, b_text: str, use_case: bool):
    i = j = 0
    cclass = 0
    len_a, len_b = len(a_text), len(b_text)
    ca = cb = '\0'
    while True:
        if i < len_a:
            ca_orig = a_text[i]; i += 1
        else:
            ca_orig = '\0'
        if j < len_b:
            cb_orig = b_text[j]; j += 1
        else:
            cb_orig = '\0'

        ca = ca_orig if use_case else ca_orig.lower()
        cb = cb_orig if use_case else cb_orig.lower()

        if ca != cb:
            break

        cls = _char_class(ca)
        cclass = _state_machine[cclass * N_CHAR_CLASS + cls]

        if ca == '\0':
            break

    if cclass in (0, 1) and ca.isdigit() and cb.isdigit():
        cclass = 2

    if cclass in (2, 3):

        if ca.isdigit():
            if cb.isdigit():
        
                acnt = 0
                while i < len_a and a_text[i].isdigit():
                    acnt += 1; i += 1
                bcnt = 0
                while j < len_b and b_text[j].isdigit():
                    bcnt += 1; j += 1
                result = acnt - bcnt
                if result == 0:
                    result = ord(ca) - ord(cb)
            else:
                result = 1
        elif cb.isdigit():
            result = -1
        elif ca == '.':
            result = 1
        elif cb == '.':
            result = -1
        else:
            result = ord(ca) - ord(cb)
            cclass = 2
        if cclass == 3:
            result = -result

    elif cclass in (0, 1, 4):
        result = ord(ca) - ord(cb)

    elif cclass == 5:
        result = ord(cb) - ord(ca)

    else:
        result = ord(ca) - ord(cb)

    return result

def compare(a_text: str, b_text: str):
    res = _private_str_cmp(a_text, b_text, use_case=False)
    if res == 0:
        res = _private_str_cmp(a_text, b_text, use_case=True)
    return res


# ** 이 루틴은 정렬에 사용됩니다. 각 키는 하나 이상의 널로 종료된
# ** 문자열 리스트입니다. 리스트는 연속된 두 개의 널 문자로 종료됩니다.
# ** 예를 들어, 다음 텍스트는 세 개의 문자열을 가진 키입니다:
# **
# **            +one\000-two\000+three\000\000
# **
# ** 두 인수는 동일한 개수의 문자열을 가집니다. 이 루틴은 첫 번째 인수가
# ** 두 번째 인수보다 작으면 음수, 같으면 0, 크면 양수를 반환합니다.
# ** (결과는 a-b입니다).
# **
# ** 모든 문자열은 '+' 또는 '-' 문자로 시작합니다. 문자가 '-'이면
# ** 반환값의 부호를 반전시킵니다. 이는 내림차순 정렬을 구현하기 위한 것입니다.
# int sqliteSortCompare(const char *a, const char *b)
def sortCompare(a, b) -> int:
    res = 0
    firstA = a[0]
    while res == 0 and a and b:
        lenA = a.find('\000')
        lenB = b.find('\000')
        res = compare(a[1:lenA], b[1:lenB])
        if res == 0:
            a = a[lenA+1:]
            b = b[lenA+1:]

    if firstA == '-':
        res = -res
    
    return res

if __name__ == "__main__":
    tests = [
        ("file1.txt", "file2.txt", False),
        ("item10",    "item2",    False),
        ("a-1.5",     "a-1.10",   False),
        ("Hello",     "hello",    False),
        ("Hello",     "hello",    True),
    ]
    for a, b, uc in tests:
        print(a, b, uc, "->", _private_str_cmp(a, b, uc))