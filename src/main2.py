from parse2 import parser
from tokenizer2 import lexer

def main():
#     # Test it out
#     data = '''CREATE TABLE test'''
#
#     # Give the lexer some input
#     lexer.input(data)
#
#     # Tokenize
#     while True:
#         tok = lexer.token()
#         if not tok:
#             break  # No more input
#         print(tok)
#
    while True:
        try:
            s = input('sql > ')
        except EOFError:
            break
        if not s: continue
        result = parser.parse(s, debug=True)
        print(result)

if __name__ == '__main__':
    main()