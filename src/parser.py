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

    def cycle_start(self, num: int):
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

    @classmethod
    def is_gcode(cls, block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return not (cls.is_macro(block) or cls.is_substitution(block))

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
    def is_substitution(block: str) -> bool:
        """事前にParse.prepare()使用の事"""
        return "=" in block


class Reader:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.index = []


