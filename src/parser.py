from enum import Enum
import re
from typing import Generator

from cnc import State, RunTimeNCError
from programs import InvalidProgramNumberNCError


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
        """事前にParse.prepare()使用の事"""
        return re.sub("[^A-Z0-9.#=+\-*/[\]]", "", block)

    class CodeType(Enum):
        GCODE = None
        MACRO = None
        SUBSTITUTION = None

    @classmethod
    def which_type(cls, block: str) -> CodeType:
        if cls.is_substitution(block):
            return cls.CodeType.SUBSTITUTION
        elif cls.is_macro(block):
            return cls.CodeType.MACRO
        else:
            return cls.CodeType.GCODE

    @staticmethod
    def is_substitution(block: str) -> bool:
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

    @classmethod
    def is_gcode(cls, block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return not (cls.is_macro(block) or cls.is_substitution(block))

    @classmethod
    def encode_substitution(cls, block: str) -> list:
        """事前にParse.prepare()使用の事"""
        eq = re.search("=", block)
        if eq is None:
            raise RunTimeNCError

        add = re.search("#(.*)", block[:eq.start()])
        if add is None:
            raise MissingAddressNCError("#")

        val = block[eq.end():]
        val = cls.solve_val(val)
        return [add.group(1), eq.group(), val]

    @classmethod
    def solve_val(cls, block: str) -> float:
        ...

    @classmethod
    def solve_bool(cls, block):



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
                raise EndOfProgramNCError
            block = Parser.prepare(block)


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



