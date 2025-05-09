import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tokenizer import *
from parse import *

db = sqlite()
db.pBe = Dbbe()
pParse = Parse()
pParse.db = db
set_parse_object(pParse)
sql_text = "SELECT * FROM tableA"
result = parser.parse(sql_text, lexer = lexer)
