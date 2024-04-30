class Programs:
    def __init__(self):
        self.programs = {}

    def input_programs(self, programs: str):
        def split_in_comment(program: str) -> bool:
            for s in program:
                if s == ")":
                    return True
                elif s == "(":
                    return False
            else:
                return False
        # プログラムを"O"で分割
        split_o = programs.split("O")

        # コメント内で分割してた場合は結合
        for program in split_o:
            if split_in_comment(program):
                index = split_o.index(program)
                split_o[index - 1] += split_o[index]
                split_o.pop(index)

        # プログラムナンバーを取得しself.programsに追加
        for program in split_o:
            self.programs[int(program[1:5])] = program.splitlines()

    def is_exist(self, num: int):
        return num in self.programs.keys()

    def read(self, num: int) -> list:
        return self.programs[num]

    def read_line(self, num: int, line: int) -> str:
        return self.programs[num][line]
