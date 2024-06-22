class Positions:
    def __init__(self):
        self.positions = []


class Modal:
    def __init__(self):
        self.main_program_ = 0
        self.gr1_ = 0
        self.gr2_ = 17
        self.gr3_ = 91
        self.gr4_ = 22
        self.gr5_ = 94
        self.gr6_ = 21
        self.gr7_ = 40
        self.gr8_ = 49
        self.gr9_ = 80
        self.gr10_ = 98
        self.gr11_ = 50
        self.gr12_ = 67
        self.gr13_ = 97
        self.gr14_ = 54
        self.gr15_ = 64
        self.gr16_ = 69
        self.gr17_ = 15
        self.gr19_ = 151  # 初期値要確認
        self.gr20_ = 160  # 初期値要確認

        self.g10 = False
        self.g52 = [0, 0, 0, 0, 0]
        self.g68 = [0, 0, 0, 0, 0]

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

    @property
    def gr1(self):
        return self.gr1_

    @gr1.setter
    def gr1(self, val: int):
        assert val in {0, 1, 2, 3, 33, 75, 77, 78, 79}
        self.gr1_ = val

    @property
    def gr2(self):
        return self.gr2_

    @gr2.setter
    def gr2(self, val: int):
        assert val in {17, 18, 19}
        self.gr2_ = val

    @property
    def gr3(self):
        return self.gr3_

    @gr3.setter
    def gr3(self, val: int):
        assert val in {90, 91}
        self.gr3_ = val

    @property
    def gr4(self):
        return self.gr4_

    @gr4.setter
    def gr4(self, val: int):
        assert val in {22, 23}
        self.gr4_ = val

    @property
    def gr5(self):
        return self.gr5_

    @gr5.setter
    def gr5(self, val: int):
        assert val in {94, 95}
        self.gr5_ = val

    @property
    def gr6(self):
        return self.gr6_

    @gr6.setter
    def gr6(self, val: int):
        assert val in {20, 21}
        self.gr6_ = val

    @property
    def gr7(self):
        return self.gr7_

    @gr7.setter
    def gr7(self, val: int):
        assert val in {40, 41, 42}
        self.gr7_ = val

    @property
    def gr8(self):
        return self.gr8_

    @gr8.setter
    def gr8(self, val: int):
        assert val in {43, 44, 49}
        self.gr8_ = val

    @property
    def gr9(self):
        return self.gr9_

    @gr9.setter
    def gr9(self, val: int):
        assert val in {73, 74, 76, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89}
        self.gr9_ = val

    @property
    def gr10(self):
        return self.gr10_

    @gr10.setter
    def gr10(self, val: int):
        assert val in {98, 99}
        self.gr10_ = val

    @property
    def gr11(self):
        return self.gr11_

    @gr11.setter
    def gr11(self, val: int):
        assert val in {50, 51}
        self.gr11_ = val

    @property
    def gr12(self):
        return self.gr12_

    @gr12.setter
    def gr12(self, val: int):
        assert val in {66, 67}
        self.gr12_ = val

    @property
    def gr13(self):
        return self.gr13_

    @gr13.setter
    def gr13(self, val: int):
        assert val in {96, 97}
        self.gr13_ = val

    @property
    def gr14(self):
        return self.gr14

    @gr14.setter
    def gr14(self, val: int):
        assert val in {54, 54.1, 55, 56, 57, 58, 59}
        self.gr14_ = val

    @property
    def gr15(self):
        return self.gr15_

    @gr15.setter
    def gr15(self, val: int):
        assert val in {61, 62, 63, 64}
        self.gr15_ = val

    @property
    def gr16(self):
        return self.gr16_

    @gr16.setter
    def gr16(self, val: int):
        assert val in {68, 69}
        self.gr16_ = val

    @property
    def gr17(self):
        return self.gr17_

    @gr17.setter
    def gr17(self, val: int):
        assert val in {15, 16}
        self.gr17_ = val

    @property
    def gr19(self):
        return self.gr19_

    @gr19.setter
    def gr19(self, val: int):
        assert val in {151, 152}
        self.gr19_ = val

    @property
    def gr20(self):
        return self.gr20_

    @gr20.setter
    def gr20(self, val: int):
        assert val in {160, 161}
        self.gr20_ = val


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



