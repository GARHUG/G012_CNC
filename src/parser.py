import re
from typing import Generator

from cnc import State
from programs import Programs, InvalidProgramNumberNCError
from variables import Variables

class Parser:
    def __init__(self, state: State):
        self.state = state
        self.g29 = [0, 0, 0, 0, 0]
        self.g66_arg = []

    def mdi(self, program: str) -> tuple:
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
        keywords = {"=", "GOTO", "IF", "WHILE", "DO", "END"}
        for keyword in keywords:
            if keyword in block:
                return True
        else:
            return False

    def call_subprogram(self, block: str):
        # self.prepare(block)使用の事
        pattern = re.search(".*(M98|G65|G66)([^0-9]|$)", block).group(1)
        # arg_p = re.search(".*(M98|G65|G66)([^0-9]|$)", block).group(1)
        self.state.variables.create_variables()
        if pattern in {"G65", "G66"}:
            args_address_key = {("A", 1), ("B", 1), ("C", 3),
                            ("I", 4), ("J", 5), ("K", 6),
                            ("D", 7), ("E", 8), ("F", 9),
                            ("H", 11), ("M", 13), ("Q", 17),
                            ("R", 18), ("S", 19), ("T", 20),
                            ("U", 21), ("V", 22), ("W", 23),
                            ("X", 24), ("Y", 25), ("Z", 26)}
            block_list = re.findall("([A-Z])([^A-Z]+)", block)
            used_arg_address = {e[0] for e in block_list}

            # all args
            if used_arg_address.intersection({e[0] for e in args_address_key}.difference({"A", "B", "C", "I", "J", "K"})):
                for add, key in args_address_key:
                    if p := re.search(f".*{add}([^A-Z]+)", block):
                        self.state.variables.write(key, p.group(1))

            # A B C I J K only args
            else:
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
                            raise OverFlowingArgumentNCError("I")
                        self.state.variables.write(key, float(val))
                        ijk_counter[0] += 1
                    if add == "J":
                        key = ijk_counter[0] * 3 + 5
                        if 33 < key:
                            raise OverFlowingArgumentNCError("I")
                        self.state.variables.write(key, float(val))
                        ijk_counter[1] += 1
                    if add == "K":
                        key = ijk_counter[0] * 3 + 6
                        if 33 < key:
                            raise OverFlowingArgumentNCError("I")
                        self.state.variables.write(key, float(val))
                        ijk_counter[2] += 1


class Reader:
    MAX_DEPTH = 100

    def __init__(self, depth: int, parser: Parser):
        if Reader.MAX_DEPTH < depth:
            raise DepthOverNCError(Reader.MAX_DEPTH)
        self.depth = 0
        self.parser = parser
        self.program = 0
        self.index = 0

        self.g66_block_memo = None
        self.loop_num_memo = None

    def cycle_start(self, program: int, index: int) -> Generator:
        self.program = program
        self.index = index
        for block in self.next():
            yield block

    def next(self) -> Generator:
        while True:
            block = self.parser.state.programs.read_block(self.program, self.index)
            block = Parser.prepare(block)
            index = [self.index]

            # macro
            if Parser.is_macro(block):
                # GOTO
                if pat_goto := re.search("GOTO([0-9]+)", block):
                    goto = int(pat_goto.group(1))
                    for i, block in enumerate(self.parser.state.programs.read(self.program)[
                                              self.index + 1:]):
                        block = Parser.prepare(block)
                        if goto == Parser.n_from_block(block):
                            self.index += i
                            break
                    else:
                        for i, block in enumerate(
                                self.parser.state.programs.read()[
                                :self.index]):
                            block = Parser.prepare(block)
                            if goto == Parser.n_from_block(block):
                                self.index = i
                                break
                        else:
                            raise MissingSequenceNCError(goto)

                # IF
                elif ...:
                    ...

                # WHILE
                elif ...:
                    ...

                # END
                elif ...:
                    ...

                # =
                elif ...:
                    ...

            # Gcode
            else:
                # 空行
                if len(block) == 0:
                    pass

                # M02, M30
                elif re.search(".*(M2|M02|M30)([^0-9]|$)", block):
                    return block

                # M99
                elif re.search(".*M99([^0-9]|$)", block):
                    if self.depth == 0:
                        yield block
                        self.index = 0
                    else:
                        return block

                # M98 G65 G66
                elif pat := re.search(".*(M98|G65|G66)([^0-9]|$)", block):
                    for block in self.call_subprogram(block):
                        yield block
                    if pat.group(1) == "G66":
                        self.g66_block_memo = block

                else:
                    yield block

                # G66 modal
                if self.parser.state.variables.read(4012) == 66:
                    for block in self.call_subprogram(self.g66_block_memo):
                        yield block






    def call_subprogram(self, block: str) -> Generator:
        # p=プログラム番号
        try:
            p = int(re.search(".*P([0-9]+)", block).group(1))
        except AttributeError:
            raise MissingArgumentNCError("P")

        # l=呼び出し回数
        l = 1
        if (pat_l := re.search(".*L([0-9]+)", block)):
            l = int(pat_l.group(1))

        # 1回目
        yield block
        for block in Reader(self.depth + 1, self.parser).cycle_start(p, 0):
            yield block

        # 2回目以降
        for i in range(l - 1):
            self.parser.call_subprogram(block)
            for block in Reader(self.depth + 1, self.parser).cycle_start(p, 0):
                yield block


class MacroInMDINCError(Exception):
    def __str__(self):
        return "MDI中にマクロは使用出来ません．"


class OverFlowingArgumentNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}が多すぎます．"


class MissingArgumentNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"アドレス{self.arg}が足りません．"


class MissingSequenceNCError(Exception):
    def __init__(self, arg: int):
        self.arg = arg

    def __str__(self):
        return f"シーケンス番号{self.arg}が見つかりません．"


class DepthOverNCError(Exception):
    def __init__(self, arg: int):
        self.arg = arg

    def __str__(self):
        return f"呼び出し回数が{self.arg}回を超えました．"







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





