from state import State


class Reader:
    def __init__(self, parser):
        self.parser = parser

class Parser:
    def __init__(self, state: State):
        self.state = state
        self.reader = Reader(self.state)

    def cycle_start(self):
        ...

    def parse(self):
        ...