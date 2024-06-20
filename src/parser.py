"""2024.06.18"""

from enum import Enum
import math
import re
from typing import Generator

import state


class Parser:
    def __init__(self, modal: state.Modal, programs: state.Programs,
                 variables: state.Variables):
        # 参照
        self.modal = modal
        self.programs = programs
        self.variables = variables
        # メモ
        self.index = []
        self.g29 = [0, 0, 0, 0, 0]

    def mdi(self, block: str):
        self.parse(block)

    def cycle_start(self, program_num: int, row: int) -> Generator:
        if not self.programs.is_exist(program_num):
            raise NCParserError("プログラムが存在しません．")
        if self.get_while_range(program_num, row) != (-1, -1):
            raise NCParserError("WHILE文中からは開始出来ません．")
        self.index.clear()
        self.index.append({"p": program_num, "r": row})
        for block in self.next():
            self.parse(block)
            yield

    def parse(self):
        """indexを更新する"""
        block = self.programs.read_block(self.p, self.r)
        block = self.prepare(block)
        self.check_mixed_gcode_and_macro(block)
        while not block:  # 空行
            self.nl()
        # マクロ
        if self.is_sub_block(block):
            self.sub(block)
        elif self.is_goto_block(block):
            self.goto(block)
        elif self.is_if_block(block):
            self.if_(block)
        elif self.is_while_block(block):
            self.while_(block)
        elif self.is_end_block(block):
            self.end(block)
        # Gコード
        else:
            ...

    def parse_gcode(self, block):
        sb = self.split_gcode(block)
        args = self.get_ini_args()
        for a, v in sb:
            v = self.solve_value_or_none(v)
            if a == "G":
                gr = self.get_group(v)
                if gr == 1:
                    self.modal.gr1 = v


    @staticmethod
    def get_ini_args() -> dict:
        addresses = ("A", "B", "C", "D", "E", "F", "H", "I", "J", "K",
                     "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
                     "V", "W", "X", "Y", "Z",
                     "Ggr0", "Ggr1", "Ggr2", "Ggr3", "Ggr4", "Ggr5",
                     "Ggr6", "Ggr7", "Ggr8", "Ggr9", "Ggr10", "Ggr11",
                     "Ggr12", "Ggr13", "Ggr14", "Ggr15", "Ggr16",
                     "Ggr17", "Ggr19", "Ggr20")
        return {arg: [] for arg in addresses}



    def sub(self, block: str):
        sb = self.split_sub(block)
        key = self.to_int(self.solve_value(sb[0][1]))
        val = self.solve_value_or_none(sb[1][1])
        self.variables.write(key, val)
        self.nl()

    def goto(self, block: str):
        program = self.programs.read(self.p)
        target_n = self.to_int(self.solve_value(self.split_goto(block)[0][1]))
        # 下を検索
        for i, block in enumerate(program[self.r + 1:]):
            block = self.prepare(block)
            pat = re.search(f".*N({self.get_val_pat()})", block)
            if pat is None:
                continue
            n = self.to_int(self.solve_value(pat.group(1)))
            if n == target_n:
                row = self.r + i + 1
                if self.can_jump(self.p, self.r, row):
                    self.r = row
                    return
                else:
                    raise NCParserError("WHILE文中には飛べません．")
        # 上を検索
        for i, block in enumerate(program[:self.r]):
            block = self.prepare(block)
            pat = re.search(f".*N({self.get_val_pat()})", block)
            if pat is None:
                continue
            n = self.to_int(self.solve_value(pat.group(1)))
            if n == target_n:
                if self.can_jump(self.p, self.r, i):
                    self.r = i
                    return
                else:
                    raise NCParserError("WHILE文中には飛べません．")
        # 見つからない
        raise NCParserError("シーケンス番号が見つかりません．")

    def if_(self, block: str):
        sb = self.split_if(block)
        if self.solve_formula(sb[0][1]):
            if sb[1][:4] == "GOTO":
                self.goto(sb[1])
            else:
                self.sub(sb[1][4:])
                self.nl()
        else:
            self.nl()

    def while_(self, block: str):
        sb = self.split_while(block)
        do = self.to_int(self.solve_value(sb[1][1]))
        if do not in {1, 2, 3}:
            raise NCParserError("DO番号が不正です．")
        # 式がTrue
        if self.solve_formula(sb[0][1]):
            self.nl()
        # 式がFalse
        else:
            for i, block in enumerate(self.programs.read(self.p)[self.r:]):
                block = self.prepare(block)
                if self.is_end_block(block) and do == self.to_int(self.solve_value(self.split_end(block)[0][1])):
                    r = self.r + i
                    if self.can_jump(self.p, self.r, r):
                        self.r = r
                    else:
                        raise NCParserError("WHILE文中には飛べません．")

    def end(self, block: str):
        program = self.programs.read(self.p)
        target_do = self.to_int(self.solve_value(self.split_end(block)[0][1]))
        # 上を下から検索
        for i, block in enumerate(program[self.r::-1]):
            block = self.prepare(block)
            if self.is_do_block(block):
                do = self.to_int(self.solve_value(self.split_do(block)[0][1]))
                if target_do == do:
                    if self.can_jump(self.p, self.r, self.r - i):
                        self.r -= i
                        return
                    else:
                        raise NCParserError("WHILE文中には飛べません．")
        # 見つからない
        raise NCParserError("DO番号が見つかりません．")

    def nl(self):
        self.r += 1

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
            raise NCParserError(f"無効な文字が含まれています．: {block}")
        return result

    @staticmethod
    def get_group(g: float) -> int:
        if g in {4, 5, 5.1, 8, 9, 10, 11, 27, 28, 29, 30, 31, 37, 39,
                 45, 46, 47, 48, 52, 53, 60, 65, 92, 107}:
            return 0
        elif g in {0, 1, 2, 3, 33, 75, 77, 78, 79}:
            return 1
        elif g in {17, 18, 19}:
            return 2
        elif g in {90, 91}:
            return 3
        elif g in {22, 23}:
            return 4
        elif g in {94, 95}:
            return 5
        elif g in {20, 21}:
            return 6
        elif g in {40, 41, 42}:
            return 7
        elif g in {43, 44, 49}:
            return 8
        elif g in {73, 74, 76, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89}:
            return 9
        elif g in {98, 99}:
            return 10
        elif g in {50, 51}:
            return 11
        elif g in {66, 67}:
            return 12
        elif g in {96, 97}:
            return 13
        elif g in {54, 54.1, 55, 56, 57, 58, 59}:
            return 14
        elif g in {61, 62, 63, 64}:
            return 15
        elif g in {68, 69}:
            return 16
        elif g in {15, 16}:
            return 17
        elif g in {151, 152}:
            return 19
        elif g in {160, 161}:
            return 20
        else:
            raise NCParserError(f"このGコードはサポートしていません．: {g}")

    def get_while_range(self, program: int, row: int) -> tuple:
        """
        一番内側のWHILE文とEND文の行番号を返す．
        start, endの初期値は-1
        :return start, end
        """
        program = self.programs.read(program)
        for i, block1 in enumerate(program[row-1::-1]):
            i += 1
            block1 = self.prepare(block1)
            if not self.is_while_block(block1):
                continue
            do = self.to_int(self.solve_value(self.split_while(block1)[1][1]))
            for j, block2 in enumerate(program[row-i:]):
                block2 = self.prepare(block2)
                if not self.is_end_block(block2):
                    continue
                if do != self.to_int(self.solve_value(self.split_end(block2)[0][1])):
                    continue
                if i < j:
                    return row - i, row - i + j
                raise NCParserError(f"END文が見つかりません．: {program[row-i]}")
        else:
            return -1, -1

    @staticmethod
    def is_sub_block(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return "=" in block and "IF" not in block

    @staticmethod
    def is_goto_block(block: str) -> bool:
        return "GOTO" in block and "IF" not in block

    @staticmethod
    def is_if_block(block: str) -> bool:
        return ("GOTO" in block or "THEN" in block) and "IF" in block

    @staticmethod
    def is_while_block(block: str) -> bool:
        return "WHILE" in block and "DO" in block

    @staticmethod
    def is_do_block(block: str) -> bool:
        return "DO" in block

    @staticmethod
    def is_end_block(block: str):
        return "END" in block

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
            float(value)
        except ValueError:
            return False
        else:
            return True

    def is_in_while(self, program: int, row: int) -> bool:
        """WHILE文,END文はFalse.GOTO文で飛べるか？で判断．"""
        depth = 0
        for i, block in enumerate(self.programs.read(program)):
            block = self.prepare(block)
            if self.is_end_block(block):
                depth -= 1
            if row == i:
                return depth == 0
            if self.is_while_block(block):
                depth += 1

    @classmethod
    def check_mixed_gcode_and_macro(cls, block: str):
        is_macro = False
        if cls.is_sub_block(block):
            is_macro = True
            block = re.sub(cls.get_sub_pat(), "", block)
        if cls.is_goto_block(block):
            is_macro = True
            block = re.sub(cls.get_goto_pat(), "", block)
        if cls.is_if_block(block):
            is_macro = True
            block = re.sub(cls.get_if_pat(), "", block)
        if cls.is_while_block(block):
            is_macro = True
            block = re.sub(cls.get_while_pat(), "", block)
        if cls.is_do_block(block):
            is_macro = True
            block = re.sub(cls.get_do_pat(), "", block)
        if cls.is_end_block(block):
            is_macro = True
            block = re.sub(cls.get_end_pat(), "", block)
        if not is_macro:
            return
        block = re.sub(f"N{cls.get_val_pat()}", "", block)
        block = re.sub(f"O{cls.get_val_pat()}", "", block)
        if block:
            raise NCParserError("Gコードとマクロが混在しています．")

    def can_jump(self, program: int, row1: int, row2):
        """プログラム番号{program}の行{row1}から行{row2}にGOTO,ENDで飛べるか？"""
        s1, e1 = self.get_while_range(program, row1)
        s2, e2 = self.get_while_range(program, row2)
        return s1 >= s2 and e1 <= e2

    @classmethod
    def split_sub(cls, block: str) -> list:
        """return: [("#", 値), ("=", 値)]"""
        enc = re.findall(cls.get_sub_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効な代入文です．: {block}")
        return cls.split_len_check(block, [("#", enc[0][0]), ("=", enc[0][3])])

    @classmethod
    def split_goto(cls, block: str) -> list:
        """return: [("GOTO", 値)]"""
        enc = re.findall(cls.get_goto_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効なGOTO文です．: {block}")
        return cls.split_len_check(block, [("GOTO", enc[0][0])])

    @classmethod
    def split_if(cls, block: str) -> list:
        """return: [("IF", 式), (マクロ命令)]"""
        enc = re.findall(cls.get_if_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効なIF文です．: {block}")
        fml = enc[0][0]
        if fml[0] != "[" or fml[-1] != "]":
            raise NCParserError(f"式がカッコに囲まれていません．: {block}")
        return cls.split_len_check(block, [("IF", fml), (enc[0][3])])

    @classmethod
    def split_while(cls, block: str) -> list:
        """return: [("WHILE", 式), ("DO", 値)]"""
        enc = re.findall(cls.get_while_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効なWHILE文です．: {block}")
        fml = enc[0][0]
        if fml[0] != "[" or fml[-1] != "]":
            raise NCParserError(f"式がカッコに囲まれていません．: {block}")
        return cls.split_len_check(block, [("WHILE", fml), ("DO", enc[0][3])])

    @classmethod
    def split_do(cls, block: str) -> list:
        """return: [("DO", 値)]"""
        enc = re.findall(cls.get_do_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効なDO文です．: {block}")
        return cls.split_len_check(block, [("DO", enc[0][0])])

    @classmethod
    def split_end(cls, block: str) -> list:
        """return: [("END", 値)]"""
        enc = re.findall(cls.get_end_pat(), block)
        if len(enc) != 1:
            raise NCParserError(f"無効なEND文です．: {block}")
        return cls.split_len_check(block, [("END", enc[0][0])])

    @classmethod
    def split_gcode(cls, block: str) -> list:
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
    def get_val_pat() -> str:
        return "([-+*/[\].#0-9]|SQRT|ABS|SIN|COS|TAN|ATAN|ROUND|FIX|FUP|BIN|BCD)+"

    @classmethod
    def get_formula_pat(cls) -> str:
        return f"({cls.get_val_pat}|EQ|NE|GT|LT|GE|LE|AND|OR)+"

    @classmethod
    def get_sub_pat(cls) -> str:
        vp = cls.get_val_pat()
        return f"#({vp})=({vp})"

    @classmethod
    def get_goto_pat(cls) -> str:
        vp = cls.get_val_pat()
        return f"GOTO({vp})"

    @classmethod
    def get_if_pat(cls) -> str:
        vp = cls.get_val_pat()
        fp = cls.get_formula_pat()
        return f"IF({fp})((THEN#{vp}={vp})|GOTO{vp})"

    @classmethod
    def get_while_pat(cls) -> str:
        vp = cls.get_val_pat()
        fp = cls.get_formula_pat()
        return f"WHILE({fp})DO({vp})"


    @classmethod
    def get_do_pat(cls) -> str:
        vp = cls.get_val_pat()
        return f"DO({vp})"

    @classmethod
    def get_end_pat(cls) -> str:
        vp = cls.get_val_pat()
        return f"END({vp})"

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
                    raise NCParserError(
                        f"マクロキーが整数ではありません．: {value}")
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
        if num is None:
            raise NCParserError("数値が#0です．")
        i = int(num)
        if i == float(num):
            return i
        else:
            raise NCParserError(f"整数化出来ません．: {num}")

    @property
    def p(self) -> int:
        return self.index[-1]["program_number"]

    @p.setter
    def p(self, val: int):
        assert isinstance(val, int)
        self.index[-1]["program_number"] = val

    @property
    def r(self):
        return self.index[-1]["row"]

    @r.setter
    def r(self, val: int):
        assert isinstance(val, int)
        self.index[-1]["row"] = val


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


class GcodeList:
    GROUP0 = {4, 4.1, 5, 5.1, 5.4, 7.1, 8, 9, 10, 10.6, 11, 24, 27, 28, 28.2,
              29, 30, 30.2, 31, 32, 39, 52, 53, 53.2, 60, 63, 65, 72.1, 72.2,
              75, 76, 77, 91.1, 92, 92.1, 107}
    GROUP1 = {0, 1, 2, 3}
    GROUP2 = {17, 18, 19}
    GROUP3 = {90, 91}
    GROUP4 = {22, 23}
    GROUP5 = {}
    GROUP6 = {20, 21, 70, 71}
    GROUP7 = {40, 41, 42}
    GROUP8 = {}
    GROUP9 = {}
    GROUP10 = {}
    GROUP11 = {50, 51}
    GROUP12 = {66, 66.1, 67}
    GROUP13 = {}
    GROUP14 = {54, 54.1, 55, 56, 57, 58, 59}
    GROUP15 = {61, 62, 64}
    GROUP16 = {68, 69, 84, 85}
    GROUP17 = {15, 16}
    GROUP18 = {40.1, 41.1, 42.1, 150, 151, 152}
    GROUP19 = {}
    GROUP20 = {}
    GROUP38 = {13, 14}
    GROUP42 = {13.2, 14.2}


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
