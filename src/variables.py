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
            self.vals[i] = 0.0

    def is_exist(self, key) -> bool:
        return key in self.vals.keys()

    def read(self, key: int) -> float:
        return self.vals[key]

    def write(self, key: int, val: float):
        self.vals[key] = val


class System:
    def __init__(self):
        self.vals = {}

    def is_exist(self, key) -> bool:
        return key in self.vals.keys()

    def read(self, key: int) -> float:
        return self.vals[key]

    def write(self, key: int, val: float):
        self.vals[key] = val


class Variables:
    def __init__(self):
        self.local = [Local()]
        self.common100 = Common100()
        self.common500 = Common500()
        self.custom = Custom()
        self.system = System()

    def is_exist(self, key) -> bool:
        if self.local[0].is_exist(key):
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
            raise KeyError

    def write(self, key: int, val: float):
        if not isinstance(val, (int, float)):
            raise ValueError
        if self.local[-1].is_exist(key):
            return self.local[-1].write(key, val)
        elif self.common100.is_exist(key):
            return self.common100.write(key, val)
        elif self.common500.is_exist(key):
            return self.common500.write(key, val)
        elif self.custom.is_exist(key):
            return self.custom.write(key, val)
        elif self.system.is_exist(key):
            return self.system.write(key, val)
        else:
            raise KeyError

    def add_local(self):
        self.local.append(Local())

    def remove_local(self):
        self.local.pop()
