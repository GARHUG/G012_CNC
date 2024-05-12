from enum import Enum
import math
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


class Bool(Enum):
    TRUE = True
    FALSE = False


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
        return result

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
    def is_logic_formula(value: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"AND", "OR"}
        for keyword in keywords:
            if keyword in value:
                return True
        else:
            return False

    @staticmethod
    def is_gcode(cls, block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return not (Parser.is_macro(block) or Parser.is_sub(block))

    @staticmethod
    def is_num(value: str, int_only: bool) -> bool:
        try:
            f = float(value)
        except ValueError:
            return False
        if int_only:
            if int(f) != f:
                return False
        return True

    @staticmethod
    def encode_sub(block: str) -> list:
        """return: [("#", 値), ("=", 値)]"""
        val_pat = Parser.get_val_pattern()
        enc = re.findall(f"#({val_pat})=({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効な代入文です．")
        return [("#", enc[0][0]), ("=", enc[0][3])]

    @staticmethod
    def encode_goto(block: str) -> list:
        """return: [("GOTO", 値)]"""
        val_pat = Parser.get_val_pattern()
        enc = re.findall(f"GOTO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なGOTO文です．")
        return [("GOTO", enc[0][0])]

    @staticmethod
    def encode_if(block: str) -> list:
        """return: [("IF", 式, マクロ命令)]"""
        val_pat = Parser.get_val_pattern()
        logic_pat = Parser.get_formula_pattern()
        enc = re.findall(f"IF({logic_pat})((THEN#{val_pat}={val_pat})|GOTO{val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なIF文です．")
        return [("IF", enc[0][0]), (enc[0][3])]

    @staticmethod
    def encode_while(block: str) -> list:
        """return: [("WHILE", 式), ("DO", 値)]"""
        val_pat = Parser.get_val_pattern()
        logic_pat = Parser.get_formula_pattern()
        enc = re.findall(f"WHILE({logic_pat})DO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なWHILE文です．")
        return [("WHILE", enc[0][0]), ("DO", enc[0][3])]

    @staticmethod
    def encode_end(block: str) -> list:
        """return: [("END", 値)]"""
        val_pat = Parser.get_val_pattern()
        enc = re.findall(f"END({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なEND文です．")
        return [("END", enc[0][0])]

    @staticmethod
    def encode_gcode(block: str) -> [(Address, float)]:
        """[(アドレス, 値)]"""
        val_pat = Parser.get_val_pattern()
        enc = re.finditer(f"([A-Z])({val_pat})", block)
        return [(ad, val) for ad, val, _ in enc]

    @staticmethod
    def encode_check_remainder(block: str, block_enc: str):
        enc = []
        for i in block_enc:
            for j in i:
                enc.append(j)
        block_enc = "".join(enc)
        if block != block_enc:
            raise NCParserError("アドレスが無効です．")

    @staticmethod
    def get_val_pattern():
        return "([-+*/[\].#0-9]|SQRT|ABS|SIN|COS|TAN|ATAN|ROUND|FIX|FUP|BIN|BCD)+"

    @staticmethod
    def get_formula_pattern():
        return f"({Parser.get_val_pattern}|EQ|NE|GT|LT|GE|LE|AND|OR)+"

    def solve(self, value: str) -> float:
        """エンコードされた値を計算"""
        # 四則演算で分割
        result = Parser.split_asmd(value)
        # 分割した要素の偶数番目を式から値に変換
        for i, val in enumerate(result[::2]):
            i = i * 2
            if Parser.is_num(val, False):
                pass
            elif val[0] == "[" and val[-1] == "]":
                result[i] = self.solve(val[1:-1])
            elif val[0] == "#":
                v = self.solve(val[1:])
                if not Parser.is_num(str(v), True):
                    raise NCParserError("マクロキーが整数ではありません．")
                result[i] = self.state.variables.read(v)
            elif val[:4] == "SQRT":
                v = self.solve(val[5:-1])
                result[i] = math.sqrt(v)
            elif val[:3] == "ABS":
                v = self.solve(val[4:-1])
                result[i] = abs(v)
            elif val[:3] == "SIN":
                v = self.solve(val[4:-1])
                result[i] = math.sin(v)
            elif val[:3] == "COS":
                v = self.solve(val[4:-1])
                result[i] = math.cos(v)
            elif val[:3] == "TAN":
                v = self.solve(val[4:-1])
                result[i] = math.tan(v)
            elif val[:4] == "ATAN":
                v = self.solve(val[5:-1])
                result[i] = math.atan(v)
            elif val[:5] == "ROUND":
                v = self.solve(val[6:-1])
                result[i] = round(v)
            elif val[:3] == "FIX":
                v = self.solve(val[4:-1])
                result[i] = math.floor(v)
            elif val[:3] == "FUP":
                v = self.solve(val[4:-1])
                result[i] = math.ceil(v)
            elif val[:3] == "BIN":
                v = self.solve(val[4:-1])
                result[i] = Parser.bin(str(v))
            elif val[:3] == "BCD":
                v = self.solve(val[4:-1])
                result[i] = Parser.bcd(str(v))
            else:
                assert False
        # 四則演算
        return eval("".join(map(str, result)))

    @staticmethod
    def split_asmd(value: str) -> list:
        result = []
        bkt_cnt = 0
        tmp = ""
        for s in value:
            if s == "[":
                bkt_cnt += 1
            elif s == "]":
                bkt_cnt -= 1
            if bkt_cnt == 0 and s in {"+", "-", "*", "/"}:
                result.append(tmp)
                result.append(s)
                tmp = ""
            else:
                tmp += s
        else:
            if bkt_cnt != 0:
                raise NCParserError("カッコが一致しません．")
        result.append(tmp)
        if not result[0]:
            result[0] = "0"
        return result

    @staticmethod
    def bcd(value: str) -> float:
        if re.search("[^01]", value):
            raise NCParserError("BCD計算出来ません．")
        q, mod = divmod(len(value), 4)
        result = 0
        # 足りない0を補充
        if mod != 0:
            value = "0" * (4 - mod) + value
            q += 1
        # 計算
        for i, j in enumerate(range(q-1, -1, -1)):
            i = i * 4
            result += int(value[i:i+4], 2) * 10 ** j
        return result

    @staticmethod
    def bin(value: str) -> float:
        if not Parser.is_num(value, True):
            raise NCParserError("BIN計算出来ません．")
        result = ""
        for s in value:
            b = bin(int(s))[2:].zfill(4)
            result += b
        return float(result)

    def solve_formula(self, formula: str) -> Bool:
        formula = Parser.split_logic(formula[1:-1])
        for b in formula[::2]:
            if not isinstance(b, Bool):

    @staticmethod
    def split_logic(formula: str) -> list:
        result = []
        bkt_cnt = 0
        tmp = ""
        for s in formula:
            if s == "[":
                if bkt_cnt == 0:
                    result.append(tmp)
                    tmp = ""
                    tmp += s
                bkt_cnt += 1
            elif s == "]":
                bkt_cnt -= 1
                if bkt_cnt == 0:
                    tmp += s
                    result.append(tmp)
                    tmp = ""
            else:
                tmp += s

        if bkt_cnt != 0:
            raise NCParserError("カッコが一致しません．")
        if not result[0]:
            del result[0]
        return result

    @staticmethod
    def calc_bool(formula: list) -> Bool:
        ...

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
