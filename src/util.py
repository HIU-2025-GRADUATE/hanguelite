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