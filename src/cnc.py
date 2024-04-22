from typing import Generator

from state import State
from parser import Parser


class CNC:
    def __init__(self):
        self.state = State()
        self.parser = Parser(self.state)

    def input_programs(self, programs: str):
        ...

    def remove_program(self, num: int):
        ...

    def input_parameter(self, num: int, parameter: tuple):
        ...

    def cycle_start(self, num: int) -> Generator:
        for state in self.parser.cycle_start(num):
            yield state
