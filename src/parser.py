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

    @classmethod
    def which_type(cls, block: str) -> CodeType:
        if cls.is_sub(block):
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
    def is_logic_formula(formula: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"AND", "OR"}
        for keyword in keywords:
            if keyword in formula:
                return True
        else:
            return False

    @classmethod
    def is_gcode(cls, block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return not (cls.is_macro(block) or cls.is_sub(block))

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

    @classmethod
    def encode_sub(cls, block: str) -> list:
        """return: [("#", 値), ("=", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"#({val_pat})=({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効な代入文です．")
        return [("#", enc[0][0]), ("=", enc[0][3])]

    @classmethod
    def encode_goto(cls, block: str) -> list:
        """return: [("GOTO", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"GOTO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なGOTO文です．")
        return [("GOTO", enc[0][0])]

    @classmethod
    def encode_if(cls, block: str) -> list:
        """return: [("IF", 式, マクロ命令)]"""
        val_pat = cls.get_val_pat()
        logic_pat = cls.get_formula_pat()
        enc = re.findall(f"IF\[({logic_pat})]((THEN#{val_pat}={val_pat})|GOTO{val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なIF文です．")
        return [("IF", enc[0][0]), (enc[0][3])]

    @classmethod
    def encode_while(cls, block: str) -> list:
        """return: [("WHILE", 式), ("DO", 値)]"""
        val_pat = cls.get_val_pat()
        logic_pat = cls.get_formula_pat()
        enc = re.findall(f"WHILE\[({logic_pat})]DO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なWHILE文です．")
        return [("WHILE", enc[0][0]), ("DO", enc[0][3])]

    @classmethod
    def encode_end(cls, block: str) -> list:
        """return: [("END", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"END({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError("無効なEND文です．")
        return [("END", enc[0][0])]

    @classmethod
    def encode_gcode(cls, block: str) -> [(Address, float)]:
        """[(アドレス, 値)]"""
        val_pat = cls.get_val_pat()
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
    def get_val_pat():
        return "([-+*/[\].#0-9]|SQRT|ABS|SIN|COS|TAN|ATAN|ROUND|FIX|FUP|BIN|BCD)+"

    @classmethod
    def get_formula_pat(cls):
        return f"({cls.get_val_pat}|EQ|NE|GT|LT|GE|LE|AND|OR)+"

    def solve_value(self, value: str) -> float:
        """エンコードされた値を計算"""
        # 四則演算で分割
        result = self.split_asmd(value)
        # 分割した要素の偶数番目を式から値に変換
        # 奇数番目は[+-*/]、偶数番目は値
        for i, val in enumerate(result[::2]):
            i = i * 2
            if self.is_num(val, False):
                pass
            elif val[0] == "[" and val[-1] == "]":
                result[i] = self.solve_value(val[1:-1])
            elif val[0] == "#":
                v = self.solve_value(val[1:])
                if not self.is_num(str(v), True):
                    raise NCParserError("マクロキーが整数ではありません．")
                result[i] = self.state.variables.read(v)
            elif val[:4] == "SQRT":
                v = self.solve_value(val[5:-1])
                result[i] = math.sqrt(v)
            elif val[:3] == "ABS":
                v = self.solve_value(val[4:-1])
                result[i] = abs(v)
            elif val[:3] == "SIN":
                v = self.solve_value(val[4:-1])
                result[i] = math.sin(v)
            elif val[:3] == "COS":
                v = self.solve_value(val[4:-1])
                result[i] = math.cos(v)
            elif val[:3] == "TAN":
                v = self.solve_value(val[4:-1])
                result[i] = math.tan(v)
            elif val[:4] == "ATAN":
                v = self.solve_value(val[5:-1])
                result[i] = math.atan(v)
            elif val[:5] == "ROUND":
                v = self.solve_value(val[6:-1])
                result[i] = round(v)
            elif val[:3] == "FIX":
                v = self.solve_value(val[4:-1])
                result[i] = math.floor(v)
            elif val[:3] == "FUP":
                v = self.solve_value(val[4:-1])
                result[i] = math.ceil(v)
            elif val[:3] == "BIN":
                v = self.solve_value(val[4:-1])
                result[i] = Parser.bin(str(v))
            elif val[:3] == "BCD":
                v = self.solve_value(val[4:-1])
                result[i] = self.bcd(str(v))
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

    def solve_formula(self, formula: str):
        """エンコードされた値を計算"""
        # 四則演算で分割
        result = self.split_logic(formula)
        # 分割した要素の偶数番目を式からbool値に変換
        # 奇数番目は[AND, OR]、偶数番目はbool値
        for i, val in enumerate(result[::2]):
            i = i * 2
            if val == True:
                pass
            elif val[0] == "[" and val[-1] == "]":
                result[i] = self.solve_value(val[1:-1])
            elif val[0] == "#":
                v = self.solve_value(val[1:])
                if not self.is_num(str(v), True):
                    raise NCParserError("マクロキーが整数ではありません．")
                result[i] = self.state.variables.read(v)
            elif val[:4] == "SQRT":
                v = self.solve_value(val[5:-1])
                result[i] = math.sqrt(v)
            elif val[:3] == "ABS":
                v = self.solve_value(val[4:-1])
                result[i] = abs(v)
            elif val[:3] == "SIN":
                v = self.solve_value(val[4:-1])
                result[i] = math.sin(v)
            elif val[:3] == "COS":
                v = self.solve_value(val[4:-1])
                result[i] = math.cos(v)
            elif val[:3] == "TAN":
                v = self.solve_value(val[4:-1])
                result[i] = math.tan(v)
            elif val[:4] == "ATAN":
                v = self.solve_value(val[5:-1])
                result[i] = math.atan(v)
            elif val[:5] == "ROUND":
                v = self.solve_value(val[6:-1])
                result[i] = round(v)
            elif val[:3] == "FIX":
                v = self.solve_value(val[4:-1])
                result[i] = math.floor(v)
            elif val[:3] == "FUP":
                v = self.solve_value(val[4:-1])
                result[i] = math.ceil(v)
            elif val[:3] == "BIN":
                v = self.solve_value(val[4:-1])
                result[i] = Parser.bin(str(v))
            elif val[:3] == "BCD":
                v = self.solve_value(val[4:-1])
                result[i] = self.bcd(str(v))
            else:
                assert False
        # 四則演算
        return eval("".join(map(str, result)))

    @staticmethod
    def split_logic(formula: str) -> list:
        result = []
        bkt_cnt = 0
        tmp = ""
        ix = 0
        while ix < len(formula):
            if formula[ix] == "[":
                bkt_cnt += 1
            elif formula[ix] == "]":
                bkt_cnt -= 1
            if bkt_cnt == 0:
                result.append(tmp)423
                tmp = ""
                if formula[ix] == "A" and formula[ix] == "N" and formula[ix] == "D":
                    result.append("AND")
                    ix += 3
                elif formula[ix] == "O" and formula[ix] == "R":
                    result.append("OR")
                    ix += 2
            else:
                tmp += formula[ix]
                ix += 1
        if bkt_cnt != 0:
            raise NCParserError("カッコが一致しません．")
        if result[0] == "AND" or result[0] == "OR" or result[-1] == "AND" or result[-1] == "OR":
            raise NCParserError("式が不正です．")
        return result

    def solve_compare(self, formula: list) -> bool:
        formula = re.search(f"({self.get_val_pat()})(EQ|NE|GT|LT|GE|LE)({self.get_val_pat()})")
        if formula is None:
            raise NCParserError("式を評価出来ません．")
        val1 = self.solve_value(formula.group(1))
        com = formula.group(2)
        val2 = self.solve_value(formula.group(3))
        if com == "EQ":
            return val1 == val2
        if com == "NE":
            return val1 != val2
        if com == "GT":
            return val1 < val2
        if com == "LT":
            return val1 > val2
        if com == "GE":
            return val1 <= val2
        if com == "LE":
            return val1 >= val2


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
