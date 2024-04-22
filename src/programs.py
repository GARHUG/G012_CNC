class Programs:
    def __init__(self):
        self.programs = {}

    def input_programs(self, programs: str):
        def is_in_com(program: str):
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
            if is_in_com(program):
                index = split_o.index(program)
                split_o[index - 1] += split_o[index]
                split_o.pop(index)

        # プログラムナンバーを取得しself.programsに追加
        for program in split_o:
            num_str = ""
            for s in program[1:]:
                if s in {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}:
                    num_str += s
                else:
                    break
            self.programs[int(num_str)] = program
