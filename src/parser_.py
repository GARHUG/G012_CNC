from enum import Enum
import re
from typing import Generator

from cnc import State, RunTimeNCError
from programs import InvalidProgramNumberNCError


class Parser:
    def __init__(self, state: State):
        self.state = state
        self.g29 = [0, 0, 0, 0, 0]
        self.g66_arg = []

    def mdi(self, program: str) -> tuple:
        program = program.splitlines(program)
        for block in program:
            if self.is_macro(block):
                raise MacroInMDINCError
            result = self.parse(block)
            yield result

    def cycle_start(self, num: int) -> tuple:
        if not self.state.programs.is_exist(num):
            raise InvalidProgramNumberNCError
        reader = Reader(self.state.programs)
        for block in reader.cycle_start(num):
            result = self.parse(block)
            yield result


    def parse(self, block: str) -> tuple:
        ...


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
    def remove_space(block: str) -> str:
        return block.replace(" ", "")

    @classmethod
    def prepare(cls, block: str) -> str:
        block = cls.remove_comments(block)
        block = cls.remove_space(block)
        block = cls.solve(block)
        block = cls.all_solve(block)
        return block

    @staticmethod
    def n_from_block(block: str) -> int:
        # self.prepare(block)使用の事
        if pat := re.search(".*N([0-9]+)"):
            return int(pat.group(1))
        else:
            return -1

    def all_solve(cls, block: str) -> str:
        ...

    @staticmethod
    def solve(val: str) -> float:
        ...

    @staticmethod
    def solve_bool(formula: str) -> bool:
        ...

    @classmethod
    def is_macro(cls, block: str) -> bool:
        # 先にself.prepare(block)使用の事
        keywords = {"GOTO", "IF", "WHILE", "DO", "END"}
        for keyword in keywords:
            if keyword in block:
                return True
        else:
            return False

    def call_subprogram(self, block: str):
        # self.prepare(block)使用の事
        pattern = re.search(".*(M98|G65|G66)([^0-9]|$)", block).group(1)
        p = re.search(".*P([0-9]+)", block).group(1)
        self.state.variables.create_local_system(p)
        if pattern in {"G65", "G66"}:
            # A B C I J K only args
            if Parser.is_ijk_args(block):
                ijk_counter = [0, 0, 0]  # [I, J, K]
                for add, val in re.findall("([ABDIJK])([^A-Z])"):
                    if add == "A":
                        self.state.variables.write(1, float(val))
                    if add == "B":
                        self.state.variables.write(2, float(val))
                    if add == "C":
                        self.state.variables.write(3, float(val))
                    if add == "I":
                        key = ijk_counter[0] * 3 + 4
                        if 33 < key:
                            raise TooManyAddressNCError("I")
                        self.state.variables.write(key, float(val))
                        ijk_counter[0] += 1
                    if add == "J":
                        key = ijk_counter[0] * 3 + 5
                        if 33 < key:
                            raise TooManyAddressNCError("J")
                        self.state.variables.write(key, float(val))
                        ijk_counter[1] += 1
                    if add == "K":
                        key = ijk_counter[0] * 3 + 6
                        if 33 < key:
                            raise TooManyAddressNCError("K")
                        self.state.variables.write(key, float(val))
                        ijk_counter[2] += 1
            # all args
            else:
                args_address_key = {("A", 1), ("B", 1), ("C", 3),
                                    ("I", 4), ("J", 5), ("K", 6),
                                    ("D", 7), ("E", 8), ("F", 9),
                                    ("H", 11), ("M", 13), ("Q", 17),
                                    ("R", 18), ("S", 19), ("T", 20),
                                    ("U", 21), ("V", 22), ("W", 23),
                                    ("X", 24), ("Y", 25), ("Z", 26)}
                for add, key in args_address_key:
                    if p := re.search(f".*{add}([^A-Z]+)", block):
                        self.state.variables.write(key, float(p.group(1)))

    def search_sequence(self, program: int, goto: int, row: int) -> int:
        # self.prepare(block)使用の事
        for i, block in enumerate(self.state.programs.read(program)[row:]):
            if goto == Parser.n_from_block(Parser.prepare(block)):
                row += i
                break
        else:
            for i, block in enumerate(self.state.programs.read()[: row]):
                if goto == Parser.n_from_block(Parser.prepare(block)):
                    row = i
                    break
            else:
                raise MissingSequenceNCError(goto)
        return row

    @staticmethod
    def is_ijk_args(block: str) -> bool:
        args_address = {"A", "B", "C", "I", "J", "K", "D", "E", "F", "H", "M",
                        "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"}
        used_address = {e for e in re.findall("([A-Z])[^A-Z]+", block)}
        return not bool(used_address.intersection(args_address.difference({"A", "B", "C", "I", "J", "K"})))

    class Type(Enum):
        GCODE = None
        SUBSTITUTE = None
        MACRO = None


class Reader:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.index = []

    def cycle_start(self, program: int, row: int) -> Generator:
        self.index.append({"program": program, "row": row})
        for block in self.next():
            yield block

    def next(self) -> Generator:
        while True:
            try:
                block = self.parser.state.programs.read_block(self.index[-1]["program"], self.index[-1]["row"])
            except IndexError:
                raise EndOfProgramNCError
            block = Parser.prepare(block)
            # self.parser.parse(block)

            # macro
            if Parser.is_macro(block):
                # GOTO
                if pat_goto := re.search("GOTO([0-9]+)", block):
                    goto = int(pat_goto.group(1))
                    self.index[-1]["row"] = self.parser.search_sequence(
                        self.index[-1]["program"], goto, self.index[-1]["row"])

                # IF
                elif ...:
                    ...

                # WHILE
                elif ...:
                    ...

                # END
                elif re.search("END([0-9])"):
                    ...

                else:
                    raise RunTimeNCError

            # Gcode
            else:
                # 空行
                if len(block) == 0:
                    self.index[-1]["row"] += 1

                # M02, M30
                elif re.search(".*(M2|M02|M30)([^0-9]|$)", block):
                    return block

                # M99
                elif re.search(".*M99([^0-9]|$)", block):
                    if len(self.index) == 1:
                        yield block
                        self.index[-1]["row"] = 0
                    else:
                        return block

                # M98 G65 G66
                elif pat := re.search(".*(M98|G65|G66)([^0-9]|$)", block):
                    if pat.group(1) == "G66":
                        self.index[-1]["g66"] = block
                    for b in self.call_subprogram(block, False):
                        if re.search(".*(M2|M02|M30)([^0-9]|$)", b):
                            return b
                        else:
                            yield b
                    self.index[-1]["row"] += 1

                else:
                    # other
                    # G67
                    if "g66" in self.index[-1].keys() and re.search(".*G67([^0-9]|$)", block):
                        del self.index[-1]["g66"]

                    yield block

                    # G66 modal
                    if "g66" in self.index[-1].keys():
                        for b in self.call_subprogram(block, True):
                            yield b
                    self.index[-1]["row"] += 1







    def call_subprogram(self, block: str, is_modal: bool) -> Generator:
        start_row = 0
        # p=プログラム番号
        if p := re.search(".*P([0-9]+)", block):
            p = int(p.group(1))
        else:
            raise MissingAddressNCError("P")

        # l=呼び出し回数
        if l := re.search(".*L([0-9]+)", block):
            l = int(l.group(1))
        else:
            l = 1

        # 1回目
        if is_modal:
            self.parser.call_subprogram(block)
        else:
            yield block
        self.index.append({"program": p, "row": start_row})
        for block in self.next():
            yield block

        # 2回目以降
        for i in range(l - 1):
            self.parser.call_subprogram(block)
            self.index[-1]["row"] = start_row
            for block in self.next():
                yield block
        self.index.pop()



class MacroInMDINCError(Exception):
    def __str__(self):
        return "MDI中にマクロは使用出来ません．"


class TooManyAddressNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}が多すぎます．"


class MissingAddressNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}が見つかりません．"


class MissingSequenceNCError(Exception):
    def __init__(self, arg: int):
        self.arg = arg

    def __str__(self):
        return f"シーケンス番号{self.arg}が見つかりません．"


class EndOfProgramNCError(Exception):
    def __str__(self):
        return "プログラム終端です．"


class InvalidAddressNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}は不正です．"


class SyntaxChecker:
    def __init__(self):
        ...

    @staticmethod
    def comment_check(block: str):
        is_in_comment = False
        for s in block:
            if is_in_comment:
                if s == "(":
                    raise ValueError  # Gcode syntax error
            else:
                if s == ")":
                    raise ValueError  # Gcode syntax error
        else:
            if is_in_comment:
                raise ValueError

    @staticmethod
    def rm_comments(block: str) -> (str, list):
        """
        ブロックのコメントを削除する
        :param block:ブロック
        :return: (コメントを削除したブロック, (削除箇所, 削除した長さ))
        """
        span = []
        while True:
            pattern = re.search(".*(\(.*?\))", block)
            if pattern is None:
                break
            start, end = pattern.span(1)
            span.append((start, end - start))
            block = block[:start] + block[end:]
        if len(span) > 1:
            span.sort()
        return block, span





