import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mylexer import *
from src.myparser import *

pParse = Parse()
set_parse_object(pParse)
sql_text = "SELECT * FROM student"
result = parser.parse(sql_text, lexer = lexer)
