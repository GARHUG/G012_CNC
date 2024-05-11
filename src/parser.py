from enum import Enum
import re
from typing import Generator

from cnc import State, NCError
from programs import InvalidProgramNumberNCError


class Address(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"
    IF = "IF"
    GOTO = "GOTO"
    THEN = "THEN"
    WHILE = "WHILE"
    DO = "DO"
    END = "END"
    SUB = "="

class CodeType(Enum):
    GCODE = None
    MACRO = None
    SUB = None


class Parser:
    def __init__(self, state: State):
        self.state = state
        self.g29 = [0, 0, 0, 0, 0]

    def mdi(self, block: str):
        ...

    def cycle_start(self, program_num: int):
        ...

    def parse(self, block: str):
        ...

    @classmethod
    def prepare(cls, block: str) -> str:
        block = cls.remove_comments(block)
        block = cls.remove_not_allow_str(block)
        return block

    @staticmethod
    def remove_comments(block: str) -> str:
        is_in_comments = False
        result = ""
        for s in block:
            if s == "(":
                is_in_comments = True
            elif s == ")":
                is_in_comments = False
            elif is_in_comments:
                pass
            else:
                result += s
        return result

    @staticmethod
    def remove_not_allow_str(block: str) -> str:
        """事前にParse.remove_comments()使用の事"""
        result = re.sub("[^A-Z0-9.#=+\-*/[\]]", "", block)
        if len(result) != len(block):
            raise NCParserError("無効な文字が含まれています．")

    @staticmethod
    def which_type(block: str) -> CodeType:
        if Parser.is_sub(block):
            return CodeType.SUB
        elif Parser.is_macro(block):
            return CodeType.MACRO
        else:
            return CodeType.GCODE

    @staticmethod
    def is_sub(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return "=" in block and not "IF" in block

    @staticmethod
    def is_macro(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"GOTO", "IF", "WHILE", "DO", "END"}
        for keyword in keywords:
            if keyword in block:
                return True
        else:
            return False

    @staticmethod
    def is_bool_formula(value: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"EQ", "NE", "GT", "LT", "GE", "LE"}
        for keyword in keywords:
            if keyword in value:
                return True
        else:
            return False

    @staticmethod
    def is_gcode(cls, block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return not (Parser.is_macro(block) or Parser.is_sub(block))

    def encode_sub(self, block: str) -> list:
        val_pat = Parser.val_pat()
        enc = re.findall(f"#({val_pat})=({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効な代入文です．")
        return [("#", enc[0][0]), ("=", enc[0][3])]

    def encode_substitution_(self, block: str) -> list:
        """return: [('#', 値), ("=", 値)]"""
        eq = re.search("=", block)
        if eq is None:
            raise NCParserError("アドレス=が見つかりません")
        ad = re.search("#(.*)", block[:eq.start()])
        if ad is None:
            raise MissingAddressNCError("#")
        val = block[eq.end():]
        val = self.solve(val)
        return [("=", ad.group(1), val)]

    def encode_goto(self, block: str) -> list:
        """return: [("GOTO", 値)]"""
        val_pat = Parser.val_pat()
        enc = re.findall(f"GOTO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なGOTO文です．")
        return [("GOTO", enc[0][0])]

    def encode_if(self, block: str) -> list:
        """return: [("IF", 式, マクロ命令)]"""
        val_pat = Parser.val_pat()
        logic_pat = Parser.logic_pat()
        enc = re.findall(f"IF({logic_pat})((THEN#{val_pat}={val_pat})|GOTO{val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なIF文です．")
        return [("IF", enc[0][0]), (enc[0][3])]

    def encode_while(self, block: str) -> list:
        """return: [("WHILE", 式), ("DO", 値)]"""
        val_pat = Parser.val_pat()
        logic_pat = Parser.logic_pat()
        enc = re.findall(f"WHILE({logic_pat})DO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なWHILE文です．")
        do = self.solve(enc[0][3])
        return [("WHILE", enc[0][0]), ("DO", enc[0][3])]

    def encode_end(self, block: str) -> list:
        """return: [("END", 値)]"""
        val_pat = Parser.val_pat()
        enc = re.findall(f"END({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なEND文です．")
        return [("END", enc[0][0])]

    def encode_gcode(self, block: str) -> [(Address, float)]:
        """[(アドレス, 値)]"""
        val_pat = Parser.val_pat()
        enc = re.finditer(f"([A-Z])({val_pat})", block)
        return [(ad, val) for ad, val, _ in enc]

    def encode_check_len(self, block: str, enc: str):
        block_enc = []
        for adval in enc:
            for i in adval:
                block_enc.append(i)
        block_enc = "".join(block_enc)
        if block != block_enc:
            raise NCParserError("アドレスが無効です．")

    @staticmethod
    def val_pat():
        return "([-+*/[\].#0-9]|SQRT|ABS|SIN|COS|TAN|ATAN|ROUND|FIX|FUP|BIN|BCD)+"

    @staticmethod
    def logic_pat():
        return f"({Parser.val_pat}|EQ|NE|GT|LT|GE|LE|AND|OR)+"

    def solve_bool(self, block) -> bool:
        ...


    def solve(self, value: str) -> float:
        """エンコードされた値を計算"""



class Reader:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.index = []

    def cycle_start(self, program_num: int, row: int) -> Generator:
        self.index.append({"program_num": program_num, "row": row})
        for block in self.next():
            yield block

    def next(self) -> Generator:
        while True:
            assert 1 <= len(self.index)
            try:
                block = self.parser.state.programs.read_block(
                    self.index[-1]["program_num"],
                    self.index[-1]["row"])
            except IndexError:
                raise EndOfProgramNCReaderError
            block = Parser.prepare(block)


class NCParserError(NCError):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg





class MissingAddressNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}が見つかりません．"


class MissingSequenceNCReaderError(Exception):
    def __init__(self, arg: int):
        self.arg = arg

    def __str__(self):
        return f"シーケンス番号{self.arg}が見つかりません．"


class EndOfProgramNCReaderError(Exception):
    def __str__(self):
        return "プログラム終端です．"


class InvalidAddressNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}は不正です．"
