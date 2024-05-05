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
    def __init__(self):
        self.vals = {
            4000: 0,  # main P
            4001: 0,  # G gr1
            4002: 17,  # G gr2
            4003: 91,  # G gr3
            4004: 22,  # G gr4
            4005: 94,  # G gr5
            4006: 21,  # G gr6
            4007: 40,  # G gr7
            4008: 49,  # G gr8
            4009: 80,  # G gr9
            4010: 98,  # G gr10
            4011: 50,  # G gr11
            4012: 67,  # G gr12
            4013: 97,  # G gr13
            4014: 54,  # G gr14
            4015: 64,  # G gr15
            4016: 69,  # G gr16
            4017: 15,  # G gr17
            4019: 15,  # G gr19
            4020: 16,  # G gr20

            4102: None,  # B
            4107: None,  # D
            4109: None,  # F
            4111: None,  # H
            4113: None,  # M
            4114: 0,  # N
            4115: 0,  # P
            4119: None,  # S
            4120: 1,  # T
        }


    def is_exist(self, key) -> bool:
        return key in self.vals.keys()

    def read(self, key: int) -> float:
        return self.vals[key]

    def write(self, key: int, val: float):
        self.vals[key] = val

    def copy(self):
        new_system = System()
        for key, val in self.vals:
            new_system.write(key, val)
        return new_system


class Variables:
    def __init__(self):
        self.local = [Local()]
        self.common100 = Common100()
        self.common500 = Common500()
        self.custom = Custom()
        self.system = [System()]

    def is_exist(self, key) -> bool:
        if self.local[-1].is_exist(key):
            return True
        elif self.common100.is_exist(key):
            return True
        elif self.common500.is_exist(key):
            return True
        elif self.custom.is_exist(key):
            return True
        elif self.system[-1].is_exist(key):
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
        elif self.system[-1].is_exist(key):
            return self.system[-1].read(key)
        else:
            raise VariableKeyNCError

    def write(self, key: int, val: float):
        if not isinstance(val, (int, float)):
            raise VariableValueNCError
        if self.local[-1].is_exist(key):
            return self.local[-1].write(key, val)
        elif self.common100.is_exist(key):
            return self.common100.write(key, val)
        elif self.common500.is_exist(key):
            return self.common500.write(key, val)
        elif self.custom.is_exist(key):
            return self.custom.write(key, bool(val))
        elif self.system[-1].is_exist(key):
            return self.system[-1].write(key, val)
        else:
            raise VariableKeyNCError(key)

    def create_variables(self):
        self.local.append(Local())
        self.system.append(self.system[-1].copy())
        self.system[-1].write(4012, 67)

    def remove_variables(self):
        self.local.pop()
        if not self.local:
            self.local.append(Local())


class VariableKeyNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"キー{self.arg}は無効です．"


class VariableValueNCError(Exception):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f"値{self.arg}は無効です．"
