class Local:
    ...


class Common100:
    ...


class Common500:
    ...


class Custom:
    ...


class System:
    ...


class Variables:
    def __init__(self):
        self.local = Local()
        self.common100 = Common100()
        self.common500 = Common500()
        self.custom = Custom()
        self.system = System()