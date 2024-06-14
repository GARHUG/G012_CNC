class Positions:
    def __init__(self):
        self.positions = []


class Modal:
    def __init__(self):
        self.main_program = 0
        self.gr1 = 0
        self.gr2 = 17
        self.gr3 = 91
        self.gr4 = 22
        self.gr5 = 94
        self.gr6 = 21
        self.gr7 = 40
        self.gr8 = 49
        self.gr9 = 80
        self.gr10 = 98
        self.gr11 = 50
        self.gr12 = 67
        self.gr13 = 97
        self.gr14 = 54
        self.gr15 = 64
        self.gr16 = 69
        self.gr17 = 15
        self.gr19 = -1  # 初期値要確認
        self.gr20 = -1  # 初期値要確認

        self.g10 = False
        self.g52 = [0, 0, 0, 0, 0]

        self.b = 0
        self.d = 0
        self.f = 0
        self.h = 0
        self.m = [-1, -1, -1]  # 初期状態要確認
        self.n = 0
        self.p = 0
        self.s = 0
        self.t = 1
        self.cc_level = 5

class Programs:
    def __init__(self):
        self.programs = {}

    def is_exist(self, num: int):
        return num in self.programs.keys()

    def read(self, num: int) -> list:
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
            if s == "%":
                continue
            if s == "(":
                is_in_comment = True
                continue
            elif s == ")":
                is_in_comment = False
                continue
            if is_in_comment:
                continue
            elif s == "O":
                result.append(programs[start: i].replace("%", "").splitlines())
                start = i
        else:
            result.append(programs[start:].replace("%", "").splitlines())
        return result

    def add_program(self, program: str):
        num = int(program[0][1:5])
        if not self.is_valid_program_number(num):
            raise self.NCProgramsError("Ｏ番号が範囲外です．")
        self.programs[num] = program

    @staticmethod
    def is_valid_program_number(num: int) -> bool:
        if 1 <= num or num <= 9999:
            return True
        else:
            return False

    class NCProgramsError(Exception):
        def __init__(self, *args):
            self.args = args

        def __str__(self):
            return self.args


class Coordinates:
    def __init__(self):
        self.coordinates = []


class Parameters:
    def __init__(self):
        ...


class ToolSettings:
    def __init__(self):
        # G10 L P
        self.offset = {(l, p): 0 for l in range(10, 14) for p in range(400)}

class Variables:
    def __init__(self, modal: Modal):
        self.local = [self.Local()]
        self.common100 = self.Common100()
        self.common500 = self.Common500()
        self.custom = self.Custom()
        self.system = self.System(modal)

    def is_exist(self, key) -> bool:
        if self.local[-1].is_exist(key):
            return True
        elif self.common100.is_exist(key):
            return True
        elif self.common500.is_exist(key):
            return True
        elif self.custom.is_exist(key):
            return True
        elif self.system.is_exist(key):
            return True
        else:
            return False

    def read(self, key: int):
        if self.local[-1].is_exist(key):
            return self.local[-1].read(key)
        elif self.common100.is_exist(key):
            return self.common100.read(key)
        elif self.common500.is_exist(key):
            return self.common500.read(key)
        elif self.custom.is_exist(key):
            return self.custom.read(key)
        elif self.system.is_exist(key):
            return self.system.read(key)
        else:
            raise self.NCVariablesError("キーの値が不正です．")

    def write(self, key: int, val: float):
        assert isinstance(val, (int, float))
        if self.local[-1].is_exist(key):
            return self.local[-1].write(key, val)
        elif self.common100.is_exist(key):
            return self.common100.write(key, val)
        elif self.common500.is_exist(key):
            return self.common500.write(key, val)
        else:
            raise self.NCVariablesError("キーの値が不正です．")

    def create_local(self, program_num: int):
        self.local.append(self.Local())

    def remove_local(self):
        self.local.pop()
        if not self.local:
            self.local.append(self.Local())

    class Local:
        def __init__(self):
            self.vals = {}
            for i in range(1, 34):
                self.vals[i] = None

        def is_exist(self, key) -> bool:
            return key in self.vals.keys()

        def read(self, key: int) -> float or None:
            return self.vals[key]

        def write(self, key: int, val: float or None):
            self.vals[key] = val

    class Common100:
        def __init__(self):
            self.vals = {}
            for i in range(100, 200):
                self.vals[i] = None

        def is_exist(self, key) -> bool:
            return key in self.vals.keys()

        def read(self, key: int) -> float or None:
            return self.vals[key]

        def write(self, key: int, val: float or None):
            self.vals[key] = val

    class Common500:
        def __init__(self):
            self.vals = {}
            for i in range(500, 1000):
                self.vals[i] = 0.0

        def is_exist(self, key) -> bool:
            return key in self.vals.keys()

        def read(self, key: int) -> float:
            return self.vals[key]

        def write(self, key: int, val: float):
            self.vals[key] = val

    class Custom:
        def __init__(self):
            self.vals = {}
            for i in range(1000, 1016):
                self.vals[i] = False

        def is_exist(self, key) -> bool:
            return key in self.vals.keys()

        def read(self, key: int) -> bool:
            return self.vals[key]

        def write(self, key: int, val: bool):
            self.vals[key] = val

    class System:
        def __init__(self, modal: Modal):
            self.modal = modal

        @staticmethod
        def is_exist(key) -> bool:
            if 4000 <= key >= 4020:
                return True
            elif key in {4102, 4107, 4109, 4111, 4113, 4114, 4115, 4119, 4120}
                return True
            else:
                return False

        def read(self, key: int) -> float:
            if key == 4000:
                return self.modal.main_program
            elif key == 4001:
                return self.modal.gr1
            elif key == 4002:
                return self.modal.gr2
            elif key == 4003:
                return self.modal.gr3
            elif key == 4004:
                return self.modal.gr4
            elif key == 4005:
                return self.modal.gr5
            elif key == 4006:
                return self.modal.gr6
            elif key == 4007:
                return self.modal.gr7
            elif key == 4008:
                return self.modal.gr8
            elif key == 4009:
                return self.modal.gr9
            elif key == 4010:
                return self.modal.gr10
            elif key == 4011:
                return self.modal.gr11
            elif key == 4012:
                return self.modal.gr12
            elif key == 4013:
                return self.modal.gr13
            elif key == 4014:
                return self.modal.gr14
            elif key == 4015:
                return self.modal.gr15
            elif key == 4016:
                return self.modal.gr16
            elif key == 4017:
                return self.modal.gr17
            elif key == 4018:
                return self.modal.gr18
            elif key == 4019:
                return self.modal.gr19
            elif key == 4020:
                return self.modal.gr20
            elif key == 4102:
                return self.modal.b
            elif key == 4107:
                return self.modal.d
            elif key == 4109:
                return self.modal.f
            elif key == 4111:
                return self.modal.h
            elif key == 4113:
                return self.modal.m
            elif key == 4114:
                return self.modal.n
            elif key == 4115:
                return self.modal.p
            elif key == 4119:
                return self.modal.s
            elif key == 4120:
                return self.modal.t

    class NCVariablesError(Exception):
        def __init__(self, *args):
            self.args = args

        def __str__(self):
            return self.args



