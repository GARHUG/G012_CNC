from enum import Enum
import math
import re
from typing import Generator

import state


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


class Parser:
    def __init__(self, modal: state.Modal, programs: state.Programs,
                 variables: state.Variables):
        self.modal = modal
        self.programs = programs
        self.variables = variables
        self.g29 = [0, 0, 0, 0, 0]
        self.index = []

    def mdi(self, block: str):
        self.parse(block)

    def cycle_start(self, program_num: int, row: int) -> Generator:
        if not self.programs.is_exist(program_num):
            raise NCParserError("プログラムが存在しません．")
        if self.is_in_while(program_num, row):
            raise NCParserError("WHILE中からは開始出来ません．")
        self.index.clear()
        self.index.append({"p": program_num, "r": row})
        for block in self.next():
            self.parse(block)
            yield

    def parse(self, block: str):
        ...

    def next(self) -> Generator:
        while True:
            block = self.get_block()
            block = self.prepare(block)
            if len(block) == 0:  # 空行
                self.index[-1]["r"] += 1
                continue

            if self.is_sub(block):
                ...

            elif self.is_goto(block):
                self.goto(block)

            elif self.s.is_if(block):
                ...
            elif self.is_while(block):
                ...

            elif self.is_end(block):
                ...

            else:
                ...

            self.index[-1]["r"] += 1

    def goto(self, block: str):
        program = self.programs.read(self.index[-1]["p"])
        target_n = self.to_int(self.solve_value(self.split_goto(block)[1]))
        # 下を検索
        for i, block in enumerate(program[self.index[-1]["r"] + 1:]):
            try:
                n = self.to_int(self.solve_value(self.search_address(block, "N")))
            except NCParserError:
                continue
            else:
                if n == target_n:
                    self.index[-1]["r"] += i + 1
                    return
        # 上を検索
        for i, block in enumerate(program[:self.index[-1]["r"]]):
            try:
                n = self.to_int(
                    self.solve_value(self.search_address(block, "N")))
            except NCParserError:
                continue
            else:
                if n == target_n:
                    self.index[-1]["r"] = i
                    return
        # 見つからない
        raise NCParserError("シーケンス番号が見つかりません．")

    @classmethod
    def prepare(cls, block: str) -> str:
        block = cls.remove_comments(block)
        block = cls.remove_not_allow_str(block)
        return block

    def search_address(self, block, address) -> str:
        pat = re.search(f".*{address}({self.get_val_pat()})", block)
        if pat is None:
            raise NCParserError(f"アドレスが見つかりません．: {block}")
        else:
            return pat.group(1)

    def get_block(self) -> str:
        try:
            block = self.programs.read_block(self.index[-1]["p"],
                                             self.index[-1]["r"])
        except IndexError:
            raise NCParserError("ファイルの終端です．")
        else:
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
            raise NCParserError(f"無効な文字が含まれています．: {block}")
        return result

    @staticmethod
    def is_macro(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"GOTO", "IF", "WHILE", "DO", "END", "="}
        for keyword in keywords:
            if keyword in block:
                return True
        else:
            return False

    @staticmethod
    def is_sub(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return "=" in block and not "IF" in block

    @staticmethod
    def is_goto(block: str) -> bool:
        if "GOTO" in block and "IF" not in block:
            return True
        else:
            return False

    @staticmethod
    def is_if(block: str) -> bool:
        if ("GOTO" in block or "THEN" in block) and "IF" in block:
            return True
        else:
            return False

    @staticmethod
    def is_while(block: str) -> bool:
        if "WHILE" in block and "DO" in block:
            return True
        else:
            return False

    @staticmethod
    def is_end(block: str):
        if "END" in block:
            return True
        else:
            return False

    @staticmethod
    def is_bool_formula(formula: str) -> bool:
        """事前にParse.prepare()使用の事"""
        keywords = {"EQ", "NE", "GT", "LT", "GE", "LE"}
        for keyword in keywords:
            if keyword in formula:
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

    @staticmethod
    def is_num(value: str) -> bool:
        try:
            f = float(value)
        except ValueError:
            return False
        else:
            return True

    def is_in_while(self, program: int, row: int) -> bool:
        for block in self.programs.read(program)[row:]:
            if self.is_end(block):
                return True
        else:
            return False

    @classmethod
    def split(cls, block: str):
        if cls.is_sub(block):
            return cls.split_sub(block)
        elif cls.is_goto(block):
            return cls.split_goto(block)
        elif cls.is_if(block):
            return cls.split_if(block)
        elif cls.is_while(block):
            return cls.split_while(block)
        elif cls.is_end(block):
            return cls.split_end(block)
        else:
            return cls.split_gcode(block)

    @classmethod
    def split_sub(cls, block: str) -> list:
        """return: [("#", 値), ("=", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"#({val_pat})=({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError(f"無効な代入文です．: {block}")
        return cls.split_len_check(block, [("#", enc[0][0]), ("=", enc[0][3])])

    @classmethod
    def split_goto(cls, block: str) -> list:
        """return: [("GOTO", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"GOTO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError(f"無効なGOTO文です．: {block}")
        return cls.split_len_check(block, [("GOTO", enc[0][0])])

    @classmethod
    def split_if(cls, block: str) -> list:
        """return: [("IF", 式), (マクロ命令)]"""
        val_pat = cls.get_val_pat()
        logic_pat = cls.get_formula_pat()
        enc = re.findall(
            f"IF({logic_pat})((THEN#{val_pat}={val_pat})|GOTO{val_pat})",
            block)
        if len(enc) != 1:
            raise NCParserError(f"無効なIF文です．: {block}")
        fml = enc[0][0]
        if fml[0] != "[" or fml[-1] != "]":
            raise NCParserError(f"式がカッコに囲まれていません．: {block}")
        return cls.split_len_check(block, [("IF", fml), (enc[0][3])])

    @classmethod
    def split_while(cls, block: str) -> list:
        """return: [("WHILE", 式), ("DO", 値)]"""
        val_pat = cls.get_val_pat()
        logic_pat = cls.get_formula_pat()
        enc = re.findall(f"WHILE({logic_pat})DO({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError(f"無効なWHILE文です．: {block}")
        fml = enc[0][0]
        if fml[0] != "[" or fml[-1] != "]":
            raise NCParserError(f"式がカッコに囲まれていません．: {block}")
        return cls.split_len_check(block, [("WHILE", fml), ("DO", enc[0][3])])

    @classmethod
    def split_end(cls, block: str) -> list:
        """return: [("END", 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.findall(f"END({val_pat})", block)
        if len(enc) != 1:
            raise NCParserError(f"無効なEND文です．: {block}")
        return cls.split_len_check(block, [("END", enc[0][0])])

    @classmethod
    def split_gcode(cls, block: str) -> [(Address, float)]:
        """[(アドレス, 値)]"""
        val_pat = cls.get_val_pat()
        enc = re.finditer(f"([A-Z])({val_pat})", block)
        return cls.split_len_check(block, [(ad, val) for ad, val, _ in enc])

    @staticmethod
    def split_len_check(block: str, block_split: list) -> list:
        join = []
        for i in block_split:
            for j in i:
                join.append(j)
        join = "".join(join)
        if block != join:
            raise NCParserError(f"アドレスが不です．: {block}")
        else:
            return block_split

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
            if self.is_num(val):
                pass
            elif val[0] == "[" and val[-1] == "]":
                result[i] = self.solve_value(val[1:-1])
            elif val[0] == "#":
                v = self.solve_value(val[1:])
                try:
                    v = self.to_int(v)
                except NCParserError:
                    raise NCParserError(f"マクロキーが整数ではありません．: {value}")
                if v == 0:
                    result[i] = 0
                else:
                    result[i] = self.variables.read(self.to_int(v))
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
                result[i] = self.bin(str(v))
            elif val[:3] == "BCD":
                v = self.solve_value(val[4:-1])
                result[i] = self.bcd(str(v))
            else:
                assert False
        # 四則演算
        return eval("".join(map(str, result)))

    def solve_value_or_none(self, value: str) -> float or None:
        if value[0] == "#" and self.solve_value(value[1:]) == 0:
            return None
        else:
            return self.solve_value(value)

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
            raise NCParserError(f"カッコが一致しません．: {value}")
        result.append(tmp)
        if not result[0]:
            result[0] = "0"
        return result

    @staticmethod
    def bcd(value: str) -> float:
        if re.search("[^01]", value):
            raise NCParserError(f"BCD計算出来ません．: {value}")
        q, mod = divmod(len(value), 4)
        result = 0
        # 足りない0を補充
        if mod != 0:
            value = "0" * (4 - mod) + value
            q += 1
        # 計算
        for i, j in enumerate(range(q - 1, -1, -1)):
            i = i * 4
            result += int(value[i:i + 4], 2) * 10 ** j
        return result

    @staticmethod
    def bin(value: str) -> float:
        try:
            Parser.to_int(value)
        except NCParserError:
            raise NCParserError(f"BIN計算出来ません．: {value}")
        result = ""
        for s in value:
            b = bin(int(s))[2:].zfill(4)
            result += b
        return float(result)

    def solve_formula(self, formula: str) -> bool:
        """エンコードされた式を評価"""
        formula = self.split_logic(formula)
        for i, f in enumerate(formula[::2]):
            i = i * 2
            if self.is_logic_formula(f):
                formula[i] = self.solve_formula(f)
            elif self.is_bool_formula(f):
                formula[i] = self.solve_bool(f)
            else:
                raise NCParserError(f"式が不正です．: {formula}")
        return self.solve_logic(formula)

    @staticmethod
    def solve_logic(formula: list) -> bool:
        # ANDを処理
        ix = 1
        while ix < len(formula):
            if formula[ix] == "AND":
                if formula[ix - 1] and formula[ix + 1]:
                    formula[ix - 1:ix + 2] = True
                else:
                    formula[ix - 1:ix + 2] = False
                ix -= 1
            else:
                ix += 2
        # ORを処理
        ix = 1
        while ix < len(formula):
            if formula[ix] == "OR":
                if formula[ix - 1] or formula[ix + 1]:
                    formula[ix - 1:ix + 2] = True
                else:
                    formula[ix - 1:ix + 2] = False
                ix -= 1
            else:
                ix += 2
        assert len(formula) == 1
        return formula[0]

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
                result.append(tmp)
                tmp = ""
                if formula[ix] == "A" and formula[ix] == "N" and formula[
                    ix] == "D":
                    result.append("AND")
                    ix += 3
                elif formula[ix] == "O" and formula[ix] == "R":
                    result.append("OR")
                    ix += 2
            else:
                tmp += formula[ix]
                ix += 1
        result.append(tmp)
        if bkt_cnt != 0:
            raise NCParserError(f"カッコが一致しません．: {formula}")
        if (result[0] == "AND" or result[0] == "OR"
                or result[-1] == "AND" or result[-1] == "OR"):
            raise NCParserError(f"式が不正です．: {formula}")
        return result

    def solve_bool(self, formula: str) -> bool:
        formula = re.search(
            f"({self.get_val_pat()})(EQ|NE|GT|LT|GE|LE)({self.get_val_pat()})",
            formula)
        if formula is None:
            raise NCParserError(f"式を評価出来ません．: {formula}")
        val1 = self.solve_value_or_none(formula.group(1))
        com = formula.group(2)
        val2 = self.solve_value_or_none(formula.group(3))
        if com == "EQ":
            return val1 == val2
        if com == "NE":
            return val1 != val2
        if val1 is None:
            val1 = 0
        if val2 is None:
            val2 = 0
        if com == "GT":
            return val1 < val2
        if com == "LT":
            return val1 > val2
        if com == "GE":
            return val1 <= val2
        if com == "LE":
            return val1 >= val2

    @staticmethod
    def to_coord(num: str) -> float:
        if "." in num:
            return float(num)
        else:
            return float(num) / 1000

    @staticmethod
    def to_int(num: str or float) -> int:
        i = int(num)
        if i == float(num):
            return i
        else:
            raise NCParserError(f"整数化出来ません．: {num}")


class Reader:
    def __init__(self, parser: Parser, state: State):
        self.parser = parser
        self.state = state
        self.index = []

    def cycle_start(self, program_num: int, row: int) -> Generator:
        self.index = []
        self.index.append({"program_num": program_num, "row": row})
        for block in self.next():
            yield block

    def next(self) -> Generator:
        while True:
            assert 1 <= len(self.index)
            try:
                block = self.state.programs.read_block(
                    self.index[-1]["program_num"],
                    self.index[-1]["row"])
            except IndexError:
                raise NCParserError("ファイルの終端です．")
            block = Parser.prepare(block)


class NCParserError(Exception):
    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return self.args


"""
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
"""
