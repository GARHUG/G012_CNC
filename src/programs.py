class Programs:
    def __init__(self):
        self.programs = {}

    def is_exist(self, num: int):
        return num in self.programs.keys()

    def read(self, num: int) -> tuple:
        return self.programs[num]

    def read_block(self, num: int, index: int) -> str:
        return self.programs[num][index]

    def input_programs(self, programs: str):
        programs = self.split_programs(programs)
        for program in programs:
            self.add_program(program)

    @staticmethod
    def split_programs(programs: str) -> list:
        is_in_comment = False
        start = 0
        result = []
        for i, s in enumerate(programs):
            if s == "(":
                is_in_comment = True
            elif s == ")":
                is_in_comment = False
            elif is_in_comment:
                pass
            elif s == "%":
                pass
            elif s == "O":
                result.append(programs[start: i])
                start = i
        else:
            result.append(programs[start:])
        return result

    def add_program(self, program: str):
        program = tuple((block for block in program.splitlines() if block != "%"))
        num = int(program[0][1:5])
        if not self.is_valid_program_number(num):
            raise InvalidProgramNumberNCError(num)
        self.programs[num] = program

    @staticmethod
    def is_valid_program_number(num: int) -> bool:
        if 1 <= num or num <= 9999:
            return True
        else:
            return False




class InvalidProgramNumberNCError(Exception):
    def __init__(self, arg: int):
        self.arg = arg

    def __str__(self):
        return f"{self.arg}は有効範囲外です．"
