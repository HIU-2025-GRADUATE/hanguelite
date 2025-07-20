def hashNoCase(z : str, n : int):
    UpperToLower = [i for i in range(256)]
    for i in range(ord('A'), ord('Z') + 1):
        UpperToLower[i] = ord(chr(i).lower())

    h = 0
    if n <= 0:
        n = len(z)

    for i in range(n):
        c = ord(z[i])
        h = (h << 3) ^ h ^ UpperToLower[c]

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
