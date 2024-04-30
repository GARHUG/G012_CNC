import re

from state import State




class Parser:
    def __init__(self, state: State):
        self.state = state

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

    @classmethod
    def is_macro(cls, block: str) -> bool:
        block = cls.remove_comments(block)
        if "=" in block:
            return True
        elif "GOTO" in block:
            return True
        elif "IF" in block:
            return True
        elif "WHILE" in block:
            return True
        else:
            return False

    @classmethod
    def is_formula(cls, block: str) -> str:
        ...


class Reader:
    def __init__(self, state: State):
        self.state = state
        self.parser = Parser(state)
        self.index = 0

    def next(self):
        ...

    def cycle_start(self):
        ...

    def parse(self):
        ...







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





