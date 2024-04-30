import re

from state import State




class Parser:
    def __init__(self, state: State):
        self.state = state

    def cycle_start(self):
        ...

    def parse(self):
        ...




class Reader:
    def __init__(self, num: int, state: State):
        self.state = state
        self.num = num
        self.index = 0

    def next(self):


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





